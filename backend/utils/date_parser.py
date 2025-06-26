"""
Date parsing utilities for the booking agent.
"""

from datetime import datetime, timedelta
from typing import Dict
import re
import pytz

def parse_date_preference(user_input: str) -> Dict:
    """
    Parse user's natural language date preference and convert to structured format.
    
    Args:
        user_input: Natural language input (e.g., "tomorrow afternoon", "next Friday", "next day")
    
    Returns:
        Dictionary with structured date information
    """
    try:
        # Use IST timezone
        ist_tz = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist_tz)
        user_input_lower = user_input.lower()
        
        # Parse date
        if "tomorrow" in user_input_lower or "next day" in user_input_lower:
            target_date = today + timedelta(days=1)
        elif "next week" in user_input_lower:
            target_date = today + timedelta(days=7)
        elif "next monday" in user_input_lower:
            days_until_monday = (0 - today.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            target_date = today + timedelta(days=days_until_monday)
        elif "next tuesday" in user_input_lower:
            days_until_tuesday = (1 - today.weekday()) % 7
            if days_until_tuesday == 0:
                days_until_tuesday = 7
            target_date = today + timedelta(days=days_until_tuesday)
        elif "next wednesday" in user_input_lower:
            days_until_wednesday = (2 - today.weekday()) % 7
            if days_until_wednesday == 0:
                days_until_wednesday = 7
            target_date = today + timedelta(days=days_until_wednesday)
        elif "next thursday" in user_input_lower:
            days_until_thursday = (3 - today.weekday()) % 7
            if days_until_thursday == 0:
                days_until_thursday = 7
            target_date = today + timedelta(days=days_until_thursday)
        elif "next friday" in user_input_lower:
            days_until_friday = (4 - today.weekday()) % 7
            if days_until_friday == 0:
                days_until_friday = 7
            target_date = today + timedelta(days=days_until_friday)
        elif "next saturday" in user_input_lower:
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7
            target_date = today + timedelta(days=days_until_saturday)
        elif "next sunday" in user_input_lower:
            days_until_sunday = (6 - today.weekday()) % 7
            if days_until_sunday == 0:
                days_until_sunday = 7
            target_date = today + timedelta(days=days_until_sunday)
        else:
            # Default to tomorrow if no specific date mentioned
            target_date = today + timedelta(days=1)
        
        # Initialize time preference and start hour
        time_preference = "business hours (9 AM - 5 PM)"
        start_hour = 10
        
        # Parse specific time first (e.g., "2 PM", "14:00")
        time_12h = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', user_input_lower)
        if time_12h:
            hour = int(time_12h.group(1))
            minute = int(time_12h.group(2)) if time_12h.group(2) else 0
            period = time_12h.group(3)
            
            # Convert to 24-hour format
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
                
            time_preference = f"specific time ({hour:02d}:{minute:02d})"
            start_hour = hour
            
        # Try 24-hour format (e.g., "14:00")
        elif (time_24h := re.search(r'(\d{1,2}):(\d{2})', user_input_lower)):
            hour = int(time_24h.group(1))
            minute = int(time_24h.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                time_preference = f"specific time ({hour:02d}:{minute:02d})"
                start_hour = hour
                
        # Fall back to general time preferences only if no specific time was found
        elif "morning" in user_input_lower:
            time_preference = "morning (9 AM - 12 PM)"
            start_hour = 9
        elif "afternoon" in user_input_lower:
            time_preference = "afternoon (1 PM - 5 PM)"
            start_hour = 13
        elif "evening" in user_input_lower:
            time_preference = "evening (5 PM - 7 PM)"
            start_hour = 17
        
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