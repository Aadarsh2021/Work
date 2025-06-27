"""
Tools for the LangGraph booking agent to interact with Google Calendar.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from langchain.tools import tool
from utils.calendar import GoogleCalendarManager
from utils.date_parser import parse_date_preference

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