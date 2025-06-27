"""
Google Calendar integration utilities for appointment booking.
Handles authentication, availability checking, and appointment creation.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz
from backend.utils.date_parser import parse_date_preference

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def to_rfc3339(dt):
    # Remove microseconds and ensure correct UTC/Z format
    s = dt.replace(microsecond=0).isoformat()
    if s.endswith('+00:00'):
        s = s[:-6] + 'Z'
    return s

class GoogleCalendarManager:
    """Manages Google Calendar operations for appointment booking."""
    
    def __init__(self, credentials_file: str = "credentials.json", use_service_account: bool = True, calendar_id: str = None):
        self.credentials_file = credentials_file
        self.use_service_account = use_service_account
        self.service = None
        # Allow calendar_id override, otherwise use default
        if calendar_id:
            self.calendar_id = calendar_id
        else:
            # For service account, set to the shared calendar's ID
            if use_service_account:
                self.calendar_id = "71195bf48e50624b978a0604e023c829ed85276a42f3134f76ed0ba0081403e1@group.calendar.google.com"
            else:
                # For OAuth, 'primary' will be replaced by the user's primary calendar
                self.calendar_id = "primary"
        self.timezone = pytz.timezone('Asia/Kolkata')  # Use IST timezone
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        try:
            if self.use_service_account:
                return self._authenticate_service_account()
            else:
                return self._authenticate_oauth()
        except Exception as e:
            print(f"Error during authentication: {e}")
            return False
    
    def _authenticate_service_account(self) -> bool:
        """Authenticate using service account credentials."""
        try:
            # First try to get credentials from environment variable
            import os
            credentials_json = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
            
            if credentials_json:
                # Use credentials from environment variable
                import json
                credentials_data = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_data, scopes=SCOPES
                )
                print("✅ Service account authentication from environment variable successful")
            elif os.path.exists(self.credentials_file):
                # Fallback to credentials file
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_file, scopes=SCOPES
                )
                print("✅ Service account authentication from file successful")
            elif os.path.exists('/etc/secrets/credentials.json'):
                # Check Render secrets location
                credentials = service_account.Credentials.from_service_account_file(
                    '/etc/secrets/credentials.json', scopes=SCOPES
                )
                print("✅ Service account authentication from Render secrets successful")
            else:
                print(f"❌ No credentials found - checked environment variable, {self.credentials_file}, and /etc/secrets/credentials.json")
                return False
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=credentials)
            return True
            
        except Exception as e:
            print(f"Service account authentication failed: {e}")
            return False
    
    def _authenticate_oauth(self) -> bool:
        """Authenticate using OAuth 2.0 flow."""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(f"Credentials file {self.credentials_file} not found")
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
                
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
                
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            
            # Get the user's primary calendar ID
            try:
                calendar_list = self.service.calendarList().list().execute()
                for calendar in calendar_list.get('items', []):
                    if calendar.get('primary', False):
                        self.calendar_id = calendar['id']
                        print(f"✅ Using primary calendar: {self.calendar_id}")
                        break
            except Exception as e:
                print(f"Warning: Could not get primary calendar, using default: {e}")
                # Fall back to primary
                self.calendar_id = "primary"
            
            return True
        except Exception as e:
            print(f"Error building calendar service: {e}")
            return False
    
    def check_availability(self, start_date: datetime, end_date: datetime, 
                          duration_minutes: int = 60) -> List[Dict]:
        """
        Check available time slots between start_date and end_date.
        
        Args:
            start_date: Start of the time range to check
            end_date: End of the time range to check
            duration_minutes: Duration of the appointment in minutes
            
        Returns:
            List of available time slots
        """
        if not self.service:
            if not self.authenticate():
                return []
        
        try:
            # Ensure timezone-aware datetime objects
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=self.timezone)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=self.timezone)
            
            # Get existing events in the time range
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=to_rfc3339(start_date),
                timeMax=to_rfc3339(end_date),
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Generate available time slots
            available_slots = self._generate_available_slots(
                start_date, end_date, events, duration_minutes
            )
            
            return available_slots
            
        except HttpError as error:
            print(f"Error checking availability: {error}")
            return []
    
    def _generate_available_slots(self, start_date: datetime, end_date: datetime,
                                 events: List[Dict], duration_minutes: int) -> List[Dict]:
        """Generate available time slots based on existing events."""
        available_slots = []
        
        # Convert to timezone-aware datetime
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=self.timezone)
        else:
            start_date = start_date.astimezone(self.timezone)
            
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=self.timezone)
        else:
            end_date = end_date.astimezone(self.timezone)
        
        # Business hours: 9 AM to 5 PM
        business_start = 9
        business_end = 17
        
        current_time = start_date
        
        while current_time < end_date:
            # Check if current time is within business hours
            if business_start <= current_time.hour < business_end:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any existing events
                is_available = True
                for event in events:
                    try:
                        # Handle different datetime formats from Google Calendar
                        event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                        event_end_str = event['end'].get('dateTime', event['end'].get('date'))
                        
                        # Parse datetime strings safely
                        if 'T' in event_start_str:
                            # Remove timezone info if present
                            if event_start_str.endswith('Z'):
                                event_start_str = event_start_str[:-1]
                            event_start = datetime.fromisoformat(event_start_str).replace(tzinfo=self.timezone)
                        else:
                            # Date-only format
                            event_start = datetime.fromisoformat(event_start_str).replace(tzinfo=self.timezone)
                        
                        if 'T' in event_end_str:
                            # Remove timezone info if present
                            if event_end_str.endswith('Z'):
                                event_end_str = event_end_str[:-1]
                            event_end = datetime.fromisoformat(event_end_str).replace(tzinfo=self.timezone)
                        else:
                            # Date-only format
                            event_end = datetime.fromisoformat(event_end_str).replace(tzinfo=self.timezone)
                        
                        # Check for overlap
                        if (current_time < event_end and slot_end > event_start):
                            is_available = False
                            break
                    except Exception as e:
                        # Skip problematic events
                        print(f"Warning: Could not parse event datetime: {e}")
                        continue
                
                if is_available and slot_end <= end_date:
                    # Create slot with both ISO format and human-readable format
                    slot = {
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'duration_minutes': duration_minutes,
                        'start_time_display': current_time.strftime('%I:%M %p'),
                        'end_time_display': slot_end.strftime('%I:%M %p'),
                        'date_display': current_time.strftime('%A, %B %d, %Y')
                    }
                    available_slots.append(slot)
            
            # Move to next 30-minute slot
            current_time += timedelta(minutes=30)
        
        return available_slots
    
    def book_appointment(self, title: str, start_time: datetime, 
                        end_time: datetime, description: str = "") -> Dict:
        """
        Book an appointment in Google Calendar.
        
        Args:
            title: Title of the appointment
            start_time: Start time of the appointment
            end_time: End time of the appointment
            description: Description of the appointment
            
        Returns:
            Dictionary with booking result
        """
        if not self.service:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
        
        try:
            # Ensure datetime objects are timezone-aware and in the correct timezone
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=self.timezone)
            else:
                # Convert to the calendar's timezone if different
                start_time = start_time.astimezone(self.timezone)
                
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=self.timezone)
            else:
                # Convert to the calendar's timezone if different
                end_time = end_time.astimezone(self.timezone)
            
            print(f"🔍 Attempting to book appointment:")
            print(f"   Title: {title}")
            print(f"   Start: {start_time.isoformat()} ({start_time.strftime('%I:%M %p')})")
            print(f"   End: {end_time.isoformat()} ({end_time.strftime('%I:%M %p')})")
            print(f"   Calendar ID: {self.calendar_id}")
            print(f"   Timezone: {self.timezone}")
            
            # Check if the time slot is still available
            availability = self.check_availability(
                start_time, 
                end_time, 
                int((end_time - start_time).total_seconds() / 60)
            )
            
            if not availability:
                return {'success': False, 'error': 'Time slot no longer available'}
            
            # Create the event with explicit timezone handling
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': str(self.timezone),
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
                'transparency': 'opaque',  # Show as busy
                'visibility': 'default',   # Default visibility
            }
            
            print(f"📅 Creating event with data: {event}")
            
            # Try to insert the event
            event_result = self.service.events().insert(
                calendarId=self.calendar_id, 
                body=event,
                sendUpdates='all'  # Send notifications to attendees
            ).execute()
            
            print(f"✅ Event created successfully!")
            print(f"   Event ID: {event_result['id']}")
            print(f"   Event Link: {event_result.get('htmlLink', 'No link')}")
            
            # Parse the returned times to ensure they match what we sent
            returned_start = event_result['start']['dateTime']
            returned_end = event_result['end']['dateTime']
            
            print(f"   Returned Start: {returned_start}")
            print(f"   Returned End: {returned_end}")
            
            return {
                'success': True,
                'event_id': event_result['id'],
                'event_link': event_result.get('htmlLink', ''),
                'start_time': returned_start,
                'end_time': returned_end,
                'calendar_id': self.calendar_id
            }
            
        except HttpError as error:
            error_details = f"HTTP Error {error.resp.status}: {error.content.decode()}"
            print(f"❌ Calendar API Error: {error_details}")
            return {'success': False, 'error': error_details}
        except Exception as e:
            print(f"❌ Unexpected error booking appointment: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_next_available_slots(self, date: datetime, count: int = 5) -> List[Dict]:
        """
        Get the next available time slots for a given date.
        
        Args:
            date: Date to check for availability
            count: Number of slots to return
            
        Returns:
            List of available time slots
        """
        start_date = date.replace(hour=9, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        # Ensure timezone-aware datetime objects
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=self.timezone)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=self.timezone)
        
        available_slots = self.check_availability(start_date, end_date)
        return available_slots[:count]
    
    def suggest_time_slots(self, user_preference: str) -> List[Dict]:
        """
        Suggest time slots based on user preference.
        
        Args:
            user_preference: Natural language preference (e.g., "tomorrow afternoon", "2 PM", "this week")
            
        Returns:
            List of suggested time slots
        """
        # Parse user preference using parse_date_preference
        parsed = parse_date_preference(user_preference)
        
        # Get target date and start hour from parsed preference
        target_date = datetime.strptime(parsed['target_date'], '%Y-%m-%d')
        start_hour = parsed['start_hour']
        
        # Handle "this week" availability requests
        if parsed.get('is_availability_request') and parsed.get('availability_period') == 'week':
            # For "this week" requests, check the next 7 days
            all_slots = []
            for i in range(7):
                check_date = target_date + timedelta(days=i)
                
                # Set business hours for each day
                start_date = check_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_date = check_date.replace(hour=17, minute=0, second=0, microsecond=0)
                
                # Ensure timezone-aware datetime objects
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=self.timezone)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=self.timezone)
                
                # Get available slots for this day
                day_slots = self.check_availability(start_date, end_date)
                
                # Add day information to slots
                for slot in day_slots:
                    slot['day_name'] = check_date.strftime('%A')
                    slot['day_date'] = check_date.strftime('%B %d')
                
                all_slots.extend(day_slots)
            
            # Sort by date and time, limit to top 10 slots
            all_slots.sort(key=lambda x: x['start'])
            return all_slots[:10]
        
        # Set window to ±1 hour around requested time for specific times
        if "specific time" in parsed['time_preference']:
            # Start searching 1 hour before requested time
            start_date = target_date.replace(hour=max(9, start_hour - 1), minute=0, second=0, microsecond=0)
            # End searching 1 hour after requested time
            end_date = target_date.replace(hour=min(17, start_hour + 1), minute=59, second=59, microsecond=0)
        else:
            # For general preferences (morning, afternoon, etc.), use wider windows
            if "morning" in parsed['time_preference']:
                start_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=12, minute=0, second=0, microsecond=0)
            elif "afternoon" in parsed['time_preference']:
                start_date = target_date.replace(hour=13, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
            elif "evening" in parsed['time_preference']:
                start_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=19, minute=0, second=0, microsecond=0)
            else:
                start_date = target_date.replace(hour=9, minute=0, second=0, microsecond=0)
                end_date = target_date.replace(hour=17, minute=0, second=0, microsecond=0)
        
        # Ensure timezone-aware datetime objects
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=self.timezone)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=self.timezone)
        
        # Get available slots within the time window
        available_slots = self.check_availability(start_date, end_date)
        
        # For specific times, sort by proximity to requested time
        if "specific time" in parsed['time_preference']:
            target_time = target_date.replace(hour=start_hour, minute=0)
            available_slots.sort(key=lambda x: abs(datetime.fromisoformat(x['start']).replace(tzinfo=None) - target_time))
        
        return available_slots 