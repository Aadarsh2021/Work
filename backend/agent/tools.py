"""
Tools for the LangGraph booking agent to interact with Google Calendar.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from langchain.tools import tool
from backend.utils.calendar import GoogleCalendarManager

# Initialize calendar manager
calendar_manager = GoogleCalendarManager()

@tool
def check_calendar_availability(start_date: str, end_date: str, duration_minutes: int = 60) -> str:
    """
    Check available time slots in the calendar for a given date range.
    
    Args:
        start_date: Start date in ISO format (YYYY-MM-DD)
        end_date: End date in ISO format (YYYY-MM-DD)
        duration_minutes: Duration of the appointment in minutes (default: 60)
    
    Returns:
        JSON string with available time slots
    """
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        available_slots = calendar_manager.check_availability(
            start_dt, end_dt, duration_minutes
        )
        
        if not available_slots:
            return "No available time slots found for the specified date range."
        
        # Format the response
        slots_info = []
        for slot in available_slots:
            start_time = datetime.fromisoformat(slot['start'])
            end_time = datetime.fromisoformat(slot['end'])
            slots_info.append({
                'start': start_time.strftime('%Y-%m-%d %H:%M'),
                'end': end_time.strftime('%Y-%m-%d %H:%M'),
                'duration': f"{slot['duration_minutes']} minutes"
            })
        
        return f"Available time slots: {slots_info}"
        
    except Exception as e:
        return f"Error checking availability: {str(e)}"

@tool
def suggest_time_slots(user_preference: str) -> str:
    """
    Suggest time slots based on user's natural language preference.
    
    Args:
        user_preference: Natural language preference (e.g., "tomorrow afternoon", "next week")
    
    Returns:
        JSON string with suggested time slots
    """
    try:
        suggested_slots = calendar_manager.suggest_time_slots(user_preference)
        
        if not suggested_slots:
            return "No available time slots found for your preference."
        
        # Format the response
        slots_info = []
        for slot in suggested_slots[:5]:  # Limit to 5 suggestions
            start_time = datetime.fromisoformat(slot['start'])
            end_time = datetime.fromisoformat(slot['end'])
            slots_info.append({
                'start': start_time.strftime('%Y-%m-%d %H:%M'),
                'end': end_time.strftime('%Y-%m-%d %H:%M'),
                'duration': f"{slot['duration_minutes']} minutes"
            })
        
        return f"Suggested time slots based on '{user_preference}': {slots_info}"
        
    except Exception as e:
        return f"Error suggesting time slots: {str(e)}"

@tool
def book_appointment(title: str, start_time: str, end_time: str, description: str = "") -> str:
    """
    Book an appointment in the calendar.
    
    Args:
        title: Title of the appointment
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS)
        end_time: End time in ISO format (YYYY-MM-DDTHH:MM:SS)
        description: Description of the appointment (optional)
    
    Returns:
        String with booking confirmation or error message
    """
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        
        result = calendar_manager.book_appointment(title, start_dt, end_dt, description)
        
        if result['success']:
            return f"Appointment booked successfully! Event ID: {result['event_id']}. " \
                   f"Start: {result['start_time']}, End: {result['end_time']}. " \
                   f"Calendar link: {result['event_link']}"
        else:
            return f"Failed to book appointment: {result['error']}"
            
    except Exception as e:
        return f"Error booking appointment: {str(e)}"

@tool
def get_next_available_slots(date: str, count: int = 5) -> str:
    """
    Get the next available time slots for a specific date.
    
    Args:
        date: Date in ISO format (YYYY-MM-DD)
        count: Number of slots to return (default: 5)
    
    Returns:
        JSON string with available time slots
    """
    try:
        target_date = datetime.fromisoformat(date)
        available_slots = calendar_manager.get_next_available_slots(target_date, count)
        
        if not available_slots:
            return f"No available time slots found for {date}."
        
        # Format the response
        slots_info = []
        for slot in available_slots:
            start_time = datetime.fromisoformat(slot['start'])
            end_time = datetime.fromisoformat(slot['end'])
            slots_info.append({
                'start': start_time.strftime('%Y-%m-%d %H:%M'),
                'end': end_time.strftime('%Y-%m-%d %H:%M'),
                'duration': f"{slot['duration_minutes']} minutes"
            })
        
        return f"Available time slots for {date}: {slots_info}"
        
    except Exception as e:
        return f"Error getting available slots: {str(e)}"

@tool
def parse_date_preference(user_input: str) -> Dict:
    """
    Parse user's natural language date preference and convert to structured format.
    
    Args:
        user_input: Natural language input (e.g., "tomorrow afternoon", "next Friday", "next day")
    
    Returns:
        Dictionary with structured date information
    """
    try:
        today = datetime.now()
        user_input_lower = user_input.lower()
        
        # Parse date
        if "tomorrow" in user_input_lower or "next day" in user_input_lower:
            target_date = today + timedelta(days=1)
        elif "next week" in user_input_lower:
            target_date = today + timedelta(days=7)
        elif "next friday" in user_input_lower:
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            target_date = today + timedelta(days=days_until_friday)
        elif "next monday" in user_input_lower:
            days_until_monday = (0 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            target_date = today + timedelta(days=days_until_monday)
        else:
            # Default to tomorrow if no specific date mentioned
            target_date = today + timedelta(days=1)
        
        # Parse time preference
        if "morning" in user_input_lower:
            time_preference = "morning (9 AM - 12 PM)"
            start_hour = 9
        elif "afternoon" in user_input_lower:
            time_preference = "afternoon (1 PM - 5 PM)"
            start_hour = 13
        elif "evening" in user_input_lower:
            time_preference = "evening (5 PM - 7 PM)"
            start_hour = 17
        else:
            time_preference = "business hours (9 AM - 5 PM)"
            start_hour = 10
        
        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'time_preference': time_preference,
            'start_hour': start_hour,
            'duration': 60  # Default 1 hour
        }
        
    except Exception as e:
        return {
            'target_date': (today + timedelta(days=1)).strftime('%Y-%m-%d'),
            'time_preference': 'business hours (9 AM - 5 PM)',
            'start_hour': 10,
            'duration': 60
        } 