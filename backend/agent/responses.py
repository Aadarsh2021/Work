"""
Enhanced response templates for the TailorTalk AI booking agent.
Designed to provide incredibly natural, engaging, and helpful conversations with perfect formatting.
"""

import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta

def greeting_response() -> str:
    """Generate a warm, engaging greeting response."""
    greetings = [
        "Hello! 👋 I'm your AI assistant, and I'm here to help you schedule appointments and manage your calendar. What can I do for you today?",
        "Hi there! 🌟 I'm excited to help you with your scheduling needs. Whether you need to book a meeting, check availability, or just chat about your calendar, I'm here for you!",
        "Welcome! ✨ I'm your personal scheduling assistant. I can help you book appointments, find available time slots, and make your calendar work better for you. What would you like to do?"
    ]
    return random.choice(greetings)

def general_greeting() -> str:
    """Generate a conversational greeting that encourages interaction."""
    return (
        "Hello! 👋 I'm your AI scheduling assistant, and I'm here to make booking appointments as easy as possible for you.\n\n"
        "**Here's what I can help you with:**\n\n"
        "• 📅 **Book appointments** - Just tell me when you'd like to meet\n"
        "• 🔍 **Check availability** - See what times work for you\n"
        "• 💡 **Suggest times** - I'll find the best slots for your schedule\n"
        "• 🎯 **Flexible scheduling** - Morning, afternoon, specific times, or anytime that works\n\n"
        "**What would you like to do?** You can say things like:\n\n"
        "• \"I need to schedule a meeting for tomorrow afternoon\"\n"
        "• \"What's my availability this week?\"\n"
        "• \"Can you find me a slot next Friday?\"\n\n"
        "Just tell me what you need, and I'll guide you through it! 😊"
    )

def slot_suggestion(slots: list, date_str: str = "") -> str:
    """Generate an engaging slot suggestion response with enhanced formatting."""
    if not slots:
        return no_availability()
    
    # Format the slots nicely
    slot_options = []
    for i, slot in enumerate(slots[:5], 1):  # Limit to 5 options
        # Use the improved display format if available
        if 'start_time_display' in slot and 'end_time_display' in slot:
            start_formatted = slot['start_time_display']
            end_formatted = slot['end_time_display']
            slot_options.append(f"**{i}.** {start_formatted} - {end_formatted}")
        else:
            # Fallback to parsing ISO format
            start_time = slot.get('start', '')
            end_time = slot.get('end', '')
            
            try:
                if 'T' in start_time:
                    start_dt = datetime.fromisoformat(start_time.replace('Z', ''))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', ''))
                    
                    # Format as "2:30 PM - 3:30 PM"
                    start_formatted = start_dt.strftime('%I:%M %p')
                    end_formatted = end_dt.strftime('%I:%M %p')
                    
                    slot_options.append(f"**{i}.** {start_formatted} - {end_formatted}")
                else:
                    slot_options.append(f"**{i}.** {start_time} - {end_time}")
            except:
                slot_options.append(f"**{i}.** {start_time} - {end_time}")
    
    date_context = f" for **{date_str}**" if date_str else ""
    
    response = (
        f"Perfect! I found some great time slots{date_context} that should work well for you: 🎯\n\n"
        f"{chr(10).join(slot_options)}\n\n"
        f"**How to choose:**\n\n"
        f"• Just reply with the **number** (like \"1\" or \"3\")\n"
        f"• Or tell me the **time** (like \"2:30 PM\")\n"
        f"• Or say \"**yes**\" if you want the first option\n\n"
        f"**Which time works best for you?** I'm ready to book it right away! 📅"
    )
    
    return response

def booking_confirmation(booking_details: dict) -> str:
    """Generate an exciting booking confirmation response with enhanced formatting."""
    date = booking_details.get('date', '')
    start_time = booking_details.get('start_time', '')
    end_time = booking_details.get('end_time', '')
    duration = booking_details.get('duration', 60)
    event_id = booking_details.get('event_id', '')
    calendar_link = booking_details.get('calendar_link', '')
    
    # Add some personality based on the time
    try:
        hour = int(start_time.split(':')[0])
        if hour < 12:
            time_mood = "🌅 Perfect for a productive morning!"
        elif hour < 17:
            time_mood = "☀️ Great afternoon slot!"
        else:
            time_mood = "🌆 Evening meeting scheduled!"
    except:
        time_mood = "✨ Excellent choice!"
    
    response = (
        f"🎉 **Booking Confirmed!** 🎉\n\n"
        f"**Your appointment is scheduled for:**\n\n"
        f"📅 **Date:** {date}\n"
        f"⏰ **Time:** {start_time} - {end_time}\n"
        f"⏱️ **Duration:** {duration} minutes\n\n"
        f"{time_mood}\n\n"
    )
    
    if calendar_link:
        response += (
            f"**📱 Calendar Link:**\n\n"
            f"[Open in Google Calendar]({calendar_link})\n\n"
        )
    
    response += (
        f"**What happens next:**\n\n"
        f"• ✅ You'll receive a calendar invitation\n"
        f"• 📧 Email reminders will be sent 24 hours and 30 minutes before\n"
        f"• 🔄 You can modify or cancel anytime through your calendar\n\n"
        f"**Need anything else?** I'm here to help with:\n\n"
        f"• 📅 Booking another appointment\n"
        f"• 🔍 Checking your availability\n"
        f"• ✏️ Modifying this meeting\n\n"
        f"Just let me know what you need! 😊"
    )
    
    return response

def clarification_needed() -> str:
    """Generate a helpful clarification request with enhanced formatting."""
    return (
        "I'd love to help you with that! 🤝\n\n"
        "**Could you give me a bit more detail?** For example:\n\n"
        "**📅 For scheduling:**\n\n"
        f"• \"I need a meeting tomorrow afternoon\"\n"
        f"• \"Can you book me for next Friday at 2 PM?\"\n"
        f"• \"I'm looking for a 30-minute slot this week\"\n\n"
        f"**🔍 For availability:**\n\n"
        f"• \"What's free on Tuesday?\"\n"
        f"• \"Show me my schedule for next week\"\n"
        f"• \"Do I have time available this afternoon?\"\n\n"
        f"**💡 For general help:**\n\n"
        f"• \"What can you help me with?\"\n"
        f"• \"How does this work?\"\n\n"
        f"**Just tell me what you need, and I'll make it happen!** ✨"
    )

def clarification_general() -> str:
    """Generate a general clarification response with enhanced formatting."""
    return (
        "I want to make sure I understand exactly what you need! 🤔\n\n"
        "**Could you be a bit more specific?** Here are some examples:\n\n"
        f"• **\"I need to schedule a meeting\"** → \"When would you like to meet?\"\n"
        f"• **\"Check my calendar\"** → \"What date or time period?\"\n"
        f"• **\"Book something\"** → \"What type of appointment and when?\"\n\n"
        f"**Or if you're not sure, just ask me:**\n\n"
        f"• \"What can you help me with?\"\n"
        f"• \"How do I book an appointment?\"\n"
        f"• \"Show me some examples\"\n\n"
        f"**I'm here to help make this as easy as possible for you!** 😊"
    )

def no_availability() -> str:
    """Generate a helpful response when no slots are available with enhanced formatting."""
    return (
        "I couldn't find any available slots for that time. 😔\n\n"
        "**But don't worry!** Here are some great alternatives:\n\n"
        f"**🔄 Try a different time:**\n\n"
        f"• \"How about tomorrow morning?\"\n"
        f"• \"What's available next week?\"\n"
        f"• \"Do you have any afternoon slots?\"\n\n"
        f"**⏰ Try a different duration:**\n\n"
        f"• \"Can we do a 30-minute meeting instead?\"\n"
        f"• \"I only need 15 minutes\"\n\n"
        f"**📅 Try a different day:**\n\n"
        f"• \"What about next Monday?\"\n"
        f"• \"Any availability this weekend?\"\n\n"
        f"**Just let me know what works better for you, and I'll find the perfect slot!** 🌟"
    )

def error_response(error_type: str = "general") -> str:
    """Generate a helpful error response with enhanced formatting."""
    if error_type == "calendar":
        return (
            "I'm having trouble accessing the calendar right now. 🔧\n\n"
            "**This usually happens when:**\n\n"
            f"• The calendar is temporarily unavailable\n"
            f"• There's a brief connection issue\n"
            f"• The calendar permissions need to be updated\n\n"
            f"**What you can try:**\n\n"
            f"• Wait a moment and try again\n"
            f"• Check your internet connection\n"
            f"• Let me know if this keeps happening\n\n"
            f"**I'll be here when you're ready to try again!** 😊"
        )
    elif error_type == "booking":
        return (
            "I wasn't able to complete the booking. 😅\n\n"
            "**This might be because:**\n\n"
            f"• The time slot was just taken by someone else\n"
            f"• There was a temporary issue with the calendar\n"
            f"• The meeting details need to be adjusted\n\n"
            f"**Let's try again:**\n\n"
            f"• Pick a different time slot\n"
            f"• Try a shorter meeting duration\n"
            f"• Choose a different day\n\n"
            f"**I'm here to help you find the perfect time!** ✨"
        )
    else:
        return (
            "Something unexpected happened. 🤔\n\n"
            "**Don't worry, this is usually temporary!** Here's what you can do:\n\n"
            f"• **Try again** - The issue might resolve itself\n"
            f"• **Be more specific** - Tell me exactly what you need\n"
            f"• **Ask for help** - I can guide you through the process\n\n"
            f"**I'm here to help you succeed!** Just let me know what you'd like to do. 😊"
        )

def help_response() -> str:
    """Generate a comprehensive help response with enhanced formatting."""
    return (
        "I'm here to help you with all your scheduling needs! 📚\n\n"
        "**🎯 What I can do for you:**\n\n"
        f"**📅 Book Appointments:**\n\n"
        f"• \"Schedule a meeting for tomorrow at 2 PM\"\n"
        f"• \"Book me for next Friday morning\"\n"
        f"• \"I need a 30-minute slot this week\"\n\n"
        f"**🔍 Check Availability:**\n\n"
        f"• \"What's my availability this week?\"\n"
        f"• \"Show me free slots for Friday\"\n"
        f"• \"Do I have time available tomorrow?\"\n\n"
        f"**💡 Get Suggestions:**\n\n"
        f"• \"Find me a good time next week\"\n"
        f"• \"What's the best slot for a 1-hour meeting?\"\n"
        f"• \"Suggest some times that work\"\n\n"
        f"**⚙️ Other Commands:**\n\n"
        f"• \"Help\" - Show this message\n"
        f"• \"Clear\" - Start a new conversation\n"
        f"• \"Cancel\" - Cancel current booking\n\n"
        f"**Just tell me what you need in natural language, and I'll guide you through it!** 😊\n\n"
        f"**What would you like to do?**"
    )

def goodbye_response() -> str:
    """Generate a friendly goodbye response with enhanced formatting."""
    goodbyes = [
        "Thanks for chatting with me! 👋 I'm here whenever you need help with your calendar. Have a great day!",
        "It was great helping you today! 🌟 Don't hesitate to come back if you need to schedule anything else. Take care!",
        "You're all set! ✨ I'm always here when you need help with appointments or scheduling. See you next time!"
    ]
    return random.choice(goodbyes)

def processing_response() -> str:
    """Generate a processing response with enhanced formatting."""
    return (
        "Perfect! Let me book that for you right now... ⏳\n\n"
        f"**Processing your appointment...**\n\n"
        f"• 📅 Checking calendar availability\n"
        f"• ✅ Confirming the time slot\n"
        f"• 📧 Creating the calendar event\n"
        f"• 🔔 Setting up reminders\n\n"
        f"**Just a moment while I get everything set up for you!** ✨"
    )

def slot_selection_confirmation(slot_number: int, slot_details: dict) -> str:
    """Generate a confirmation when user selects a slot with enhanced formatting."""
    # Use the improved display format if available
    if 'start_time_display' in slot_details and 'end_time_display' in slot_details:
        start_formatted = slot_details['start_time_display']
        end_formatted = slot_details['end_time_display']
        time_str = f"{start_formatted} - {end_formatted}"
    else:
        # Fallback to parsing ISO format
        start_time = slot_details.get('start', '')
        end_time = slot_details.get('end', '')
        
        try:
            if 'T' in start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', ''))
                end_dt = datetime.fromisoformat(end_time.replace('Z', ''))
                start_formatted = start_dt.strftime('%I:%M %p')
                end_formatted = end_dt.strftime('%I:%M %p')
                time_str = f"{start_formatted} - {end_formatted}"
            else:
                time_str = f"{start_time} - {end_time}"
        except:
            time_str = f"{start_time} - {end_time}"
    
    return (
        f"Excellent choice! 🎯\n\n"
        f"**You selected:**\n\n"
        f"📅 **Slot {slot_number}:** {time_str}\n\n"
        f"**Ready to book this appointment?**\n\n"
        f"**Just say:**\n\n"
        f"• \"**Yes**\" or \"**Book it**\" to confirm\n"
        f"• \"**No**\" to pick a different time\n"
        f"• \"**Change**\" to modify the details\n\n"
        f"**I'm ready to schedule this for you!** ✨"
    ) 