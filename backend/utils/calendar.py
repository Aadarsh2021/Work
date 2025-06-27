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
    """Convert datetime to RFC3339 format."""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    else:
        dt = dt.astimezone(pytz.UTC)
    return dt.isoformat().replace('+00:00', 'Z')

class GoogleCalendarManager:
    """Google Calendar Manager for handling appointments."""
    
    def __init__(self, use_service_account: bool = False, timezone: str = None):
        """Initialize the calendar manager.
        
        Args:
            use_service_account: Whether to use service account auth
            timezone: Optional timezone string (e.g. 'America/New_York'). If None, uses UTC
        """
        self.service = None
        self.use_service_account = use_service_account
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
        
        # Use provided timezone or default to UTC
        self.timezone = pytz.timezone(timezone) if timezone else pytz.UTC
        print(f"📅 Calendar Manager initialized with timezone: {self.timezone}")
        
        # Authenticate on initialization
        self.authenticate()
    
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API."""
        try:
            if self.use_service_account:
                # Use service account authentication
                credentials = service_account.Credentials.from_service_account_file(
                    'service-account.json',
                    scopes=SCOPES
                )
                print("✅ Service account authentication from file successful")
            else:
                # Use OAuth2 authentication
                creds = None
                if os.path.exists('token.json'):
                    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                    else:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            'credentials.json', SCOPES)
                        creds = flow.run_local_server(port=0)
                    
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                
                credentials = creds
            
            self.service = build('calendar', 'v3', credentials=credentials)
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def _ensure_timezone(self, dt: datetime) -> datetime:
        """Ensure datetime is timezone-aware with the correct timezone."""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt.astimezone(self.timezone)
    
    def _format_time_for_display(self, dt: datetime) -> str:
        """Format datetime for display with timezone information."""
        dt = self._ensure_timezone(dt)
        return f"{dt.strftime('%I:%M %p')} {dt.tzname()}"
    
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
            start_date = self._ensure_timezone(start_date)
            end_date = self._ensure_timezone(end_date)
            
            # Convert to UTC for API request
            start_utc = start_date.astimezone(pytz.UTC)
            end_utc = end_date.astimezone(pytz.UTC)
            
            # Get existing events in the time range
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=to_rfc3339(start_utc),
                timeMax=to_rfc3339(end_utc),
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
        start_date = self._ensure_timezone(start_date)
        end_date = self._ensure_timezone(end_date)
        
        # Business hours: 9 AM to 5 PM in local timezone
        business_start = 9
        business_end = 17
        
        print(f"   📅 Generating slots from {start_date.strftime('%Y-%m-%d %H:%M %Z')} to {end_date.strftime('%Y-%m-%d %H:%M %Z')}")
        print(f"   📅 Business hours: {business_start}:00 to {business_end}:00 {self.timezone}")
        print(f"   📅 Found {len(events)} existing events")
        
        current_time = start_date
        
        while current_time < end_date:
            # Check if current time is within business hours
            if business_start <= current_time.hour < business_end:
                slot_end = current_time + timedelta(minutes=duration_minutes)
                
                # Check if this slot conflicts with any existing events
                is_available = True
                for event in events:
                    try:
                        # Parse event times and convert to calendar's timezone
                        event_start = self._parse_event_datetime(event['start'])
                        event_end = self._parse_event_datetime(event['end'])
                        
                        # Check for overlap
                        if (current_time < event_end and slot_end > event_start):
                            is_available = False
                            break
                    except Exception as e:
                        print(f"Warning: Could not parse event datetime: {e}")
                        continue
                
                if is_available and slot_end <= end_date:
                    # Create slot with timezone-aware times
                    slot = {
                        'start': current_time.isoformat(),
                        'end': slot_end.isoformat(),
                        'duration_minutes': duration_minutes,
                        'start_time_display': self._format_time_for_display(current_time),
                        'end_time_display': self._format_time_for_display(slot_end),
                        'date_display': current_time.strftime('%A, %B %d, %Y'),
                        'timezone': str(self.timezone)
                    }
                    available_slots.append(slot)
            
            # Move to next 30-minute slot
            current_time += timedelta(minutes=30)
        
        print(f"   📅 Generated {len(available_slots)} available slots")
        return available_slots
    
    def _parse_event_datetime(self, event_time: Dict) -> datetime:
        """Parse event datetime from Google Calendar API response."""
        dt_str = event_time.get('dateTime', event_time.get('date'))
        
        if 'T' in dt_str:  # Full datetime
            if dt_str.endswith('Z'):
                dt = datetime.fromisoformat(dt_str[:-1]).replace(tzinfo=pytz.UTC)
            else:
                dt = datetime.fromisoformat(dt_str)
        else:  # Date only
            dt = datetime.fromisoformat(dt_str)
            dt = pytz.UTC.localize(dt)
        
        return dt.astimezone(self.timezone)
    
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
            # Ensure datetime objects are timezone-aware
            start_time = self._ensure_timezone(start_time)
            end_time = self._ensure_timezone(end_time)
            
            print(f"🔍 Attempting to book appointment:")
            print(f"   Title: {title}")
            print(f"   Start: {self._format_time_for_display(start_time)}")
            print(f"   End: {self._format_time_for_display(end_time)}")
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
                    'dateTime': to_rfc3339(start_time),
                    'timeZone': str(self.timezone)
                },
                'end': {
                    'dateTime': to_rfc3339(end_time),
                    'timeZone': str(self.timezone)
                }
            }
            
            # Insert the event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            return {
                'success': True,
                'event_id': event['id'],
                'start_time': self._format_time_for_display(start_time),
                'end_time': self._format_time_for_display(end_time),
                'timezone': str(self.timezone)
            }
            
        except HttpError as error:
            print(f"Error booking appointment: {error}")
            return {'success': False, 'error': str(error)}
    
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
        
        # Handle availability requests for "this week" or "next week"
        if parsed.get('is_availability_request') and ("week" in parsed.get('time_preference', '').lower() or parsed.get('availability_period') == 'week'):
            # For week requests, check the next 7 days
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
        
        # For specific time requests, try to match exactly first
        if "specific time" in parsed['time_preference']:
            # First try exact time match
            exact_start = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            exact_end = exact_start + timedelta(minutes=60)  # Default 1-hour slot
            
            # Ensure timezone-aware datetime objects
            if exact_start.tzinfo is None:
                exact_start = exact_start.replace(tzinfo=self.timezone)
            if exact_end.tzinfo is None:
                exact_end = exact_end.replace(tzinfo=self.timezone)
            
            # Check if exact time is available
            exact_slots = self.check_availability(exact_start, exact_end)
            if exact_slots:
                return exact_slots
            
            # If exact time not available, look in a narrower window first (±1 hour)
            narrow_start = target_date.replace(hour=max(9, start_hour - 1), minute=0, second=0, microsecond=0)
            narrow_end = target_date.replace(hour=min(17, start_hour + 1), minute=59, second=59, microsecond=0)
            
            # Ensure timezone-aware datetime objects
            if narrow_start.tzinfo is None:
                narrow_start = narrow_start.replace(tzinfo=self.timezone)
            if narrow_end.tzinfo is None:
                narrow_end = narrow_end.replace(tzinfo=self.timezone)
            
            narrow_slots = self.check_availability(narrow_start, narrow_end)
            if narrow_slots:
                # Sort by proximity to requested time
                target_time = target_date.replace(hour=start_hour, minute=0)
                narrow_slots.sort(key=lambda x: abs(datetime.fromisoformat(x['start']).replace(tzinfo=None) - target_time))
                return narrow_slots
            
            # If still no slots, try wider window (±2 hours)
            start_date = target_date.replace(hour=max(9, start_hour - 2), minute=0, second=0, microsecond=0)
            end_date = target_date.replace(hour=min(17, start_hour + 2), minute=59, second=59, microsecond=0)
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
        
        # Add debugging information
        print(f"🔍 Checking availability for '{user_preference}':")
        print(f"   Target date: {target_date}")
        print(f"   Start hour: {start_hour}")
        print(f"   Time window: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
        
        # Get available slots within the time window
        available_slots = self.check_availability(start_date, end_date)
        
        print(f"   Found {len(available_slots)} available slots")
        
        # For specific times, sort by proximity to requested time
        if "specific time" in parsed['time_preference']:
            target_time = target_date.replace(hour=start_hour, minute=0)
            available_slots.sort(key=lambda x: abs(datetime.fromisoformat(x['start']).replace(tzinfo=None) - target_time))
        
        return available_slots 