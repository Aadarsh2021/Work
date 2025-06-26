"""
Enhanced response templates for the TailorTalk AI booking agent.
Designed to provide incredibly natural, engaging, and helpful conversations.
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
        "**Here's what I can help you with:**\n"
        "• 📅 **Book appointments** - Just tell me when you'd like to meet\n"
        "• 🔍 **Check availability** - See what times work for you\n"
        "• 💡 **Suggest times** - I'll find the best slots for your schedule\n"
        "• 🎯 **Flexible scheduling** - Morning, afternoon, specific times, or anytime that works\n\n"
        "**What would you like to do?** You can say things like:\n"
        "• \"I need to schedule a meeting for tomorrow afternoon\"\n"
        "• \"What's my availability this week?\"\n"
        "• \"Can you find me a slot next Friday?\"\n\n"
        "Just tell me what you need, and I'll guide you through it! 😊"
    )

def slot_suggestion(slots: list, date_str: str = "") -> str:
    """Generate an engaging slot suggestion response."""
    if not slots:
        return no_availability()
    
    # Format the slots nicely
    slot_options = []
    for i, slot in enumerate(slots[:5], 1):  # Limit to 5 options
        start_time = slot.get('start', '')
        end_time = slot.get('end', '')
        
        # Parse and format the time
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
        f"**How to choose:**\n"
        f"• Just reply with the **number** (like \"1\" or \"3\")\n"
        f"• Or tell me the **time** (like \"2:30 PM\")\n"
        f"• Or say \"**yes**\" if you want the first option\n\n"
        f"**Which time works best for you?** I'm ready to book it right away! 📅"
    )
    
    return response

def booking_confirmation(booking_details: dict) -> str:
    """Generate an exciting booking confirmation response."""
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
        f"**Your appointment is scheduled for:**\n"
        f"📅 **Date:** {date}\n"
        f"⏰ **Time:** {start_time} - {end_time}\n"
        f"⏱️ **Duration:** {duration} minutes\n\n"
        f"{time_mood}\n\n"
    )
    
    if calendar_link:
        response += (
            f"**📱 Calendar Link:**\n"
            f"[Open in Google Calendar]({calendar_link})\n\n"
        )
    
    response += (
        f"**What happens next:**\n"
        f"• ✅ You'll receive a calendar invitation\n"
        f"• 📧 Email reminders will be sent 24 hours and 30 minutes before\n"
        f"• 🔄 You can modify or cancel anytime through your calendar\n\n"
        f"**Need anything else?** I'm here to help with:\n"
        f"• 📅 Booking another appointment\n"
        f"• 🔍 Checking your availability\n"
        f"• ✏️ Modifying this meeting\n\n"
        f"Just let me know what you need! 😊"
    )
    
    return response

def clarification_needed() -> str:
    """Generate a helpful clarification request."""
    return (
        "I'd love to help you with that! 🤝\n\n"
        "**Could you give me a bit more detail?** For example:\n\n"
        "**📅 For scheduling:**\n"
        "• \"I need a meeting tomorrow afternoon\"\n"
        "• \"Can you book me for next Friday at 2 PM?\"\n"
        "• \"I'm looking for a 30-minute slot this week\"\n\n"
        "**🔍 For availability:**\n"
        "• \"What's free on Tuesday?\"\n"
        "• \"Show me my schedule for next week\"\n"
        "• \"Do I have time available this afternoon?\"\n\n"
        "**💡 For general help:**\n"
        "• \"What can you help me with?\"\n"
        "• \"How does this work?\"\n\n"
        "**Just tell me what you need, and I'll make it happen!** ✨"
    )

def clarification_general() -> str:
    """Generate a general clarification response."""
    return (
        "I want to make sure I understand exactly what you need! 🤔\n\n"
        "**Could you be a bit more specific?** Here are some examples:\n\n"
        "• **\"I need to schedule a meeting\"** → \"When would you like to meet?\"\n"
        "• **\"Check my calendar\"** → \"What date or time period?\"\n"
        "• **\"Book something\"** → \"What type of appointment and when?\"\n\n"
        "**Or if you're not sure, just ask me:**\n"
        "• \"What can you help me with?\"\n"
        "• \"How do I book an appointment?\"\n"
        "• \"Show me some examples\"\n\n"
        "**I'm here to help make this as easy as possible for you!** 😊"
    )

def no_availability() -> str:
    """Generate a helpful response when no slots are available."""
    return (
        "I couldn't find any available slots for that time. 😔\n\n"
        "**But don't worry!** Here are some great alternatives:\n\n"
        "**🔄 Try a different time:**\n"
        "• \"How about tomorrow morning?\"\n"
        "• \"What's available next week?\"\n"
        "• \"Do you have any afternoon slots?\"\n\n"
        "**⏰ Try a different duration:**\n"
        "• \"Can we do a 30-minute meeting instead?\"\n"
        "• \"I only need 15 minutes\"\n\n"
        "**📅 Try a different day:**\n"
        "• \"What about next Monday?\"\n"
        "• \"Any availability this weekend?\"\n\n"
        "**Just let me know what works better for you, and I'll find the perfect slot!** 🌟"
    )

def error_response(error_type: str = "general") -> str:
    """Generate a helpful error response."""
    if error_type == "calendar":
        return (
            "I'm having trouble accessing the calendar right now. 🔧\n\n"
            "**This usually happens when:**\n"
            "• The calendar is temporarily unavailable\n"
            "• There's a brief connection issue\n"
            "• The calendar permissions need to be updated\n\n"
            "**What you can try:**\n"
            "• Wait a moment and try again\n"
            "• Check your internet connection\n"
            "• Let me know if this keeps happening\n\n"
            "**I'll be here when you're ready to try again!** 😊"
        )
    elif error_type == "booking":
        return (
            "I wasn't able to complete the booking. 😅\n\n"
            "**This might be because:**\n"
            "• The time slot was just taken by someone else\n"
            "• There was a temporary issue with the calendar\n"
            "• The meeting details need to be adjusted\n\n"
            "**Let's try again:**\n"
            "• Pick a different time slot\n"
            "• Try a shorter meeting duration\n"
            "• Choose a different day\n\n"
            "**I'm here to help you find the perfect time!** ✨"
        )
    else:
        return (
            "Something unexpected happened. 🤔\n\n"
            "**Don't worry, this is usually temporary!** Here's what you can do:\n\n"
            "• **Try again** - The issue might resolve itself\n"
            "• **Be more specific** - Tell me exactly what you need\n"
            "• **Ask for help** - I can guide you through the process\n\n"
            "**I'm here to help you succeed!** Just let me know what you'd like to do. 😊"
        )

def help_response() -> str:
    """Generate a comprehensive help response."""
    return (
        "I'm here to help you with all your scheduling needs! 📚\n\n"
        "**🎯 What I can do for you:**\n\n"
        "**📅 Book Appointments:**\n"
        "• \"Schedule a meeting for tomorrow at 2 PM\"\n"
        "• \"Book me for next Friday morning\"\n"
        "• \"I need a 30-minute slot this week\"\n\n"
        "**🔍 Check Availability:**\n"
        "• \"What's my availability this week?\"\n"
        "• \"Show me free slots for Friday\"\n"
        "• \"Do I have time available tomorrow?\"\n\n"
        "**💡 Get Suggestions:**\n"
        "• \"Find me a good time next week\"\n"
        "• \"What's the best slot for a 1-hour meeting?\"\n"
        "• \"Suggest some times that work\"\n\n"
        "**⚙️ Other Commands:**\n"
        "• \"Help\" - Show this message\n"
        "• \"Clear\" - Start a new conversation\n"
        "• \"Cancel\" - Cancel current booking\n\n"
        "**Just tell me what you need in natural language, and I'll guide you through it!** 😊\n\n"
        "**What would you like to do?**"
    )

def goodbye_response() -> str:
    """Generate a friendly goodbye response."""
    goodbyes = [
        "Thanks for chatting with me! 👋 I'm here whenever you need help with your calendar. Have a great day!",
        "It was great helping you today! 🌟 Don't hesitate to come back if you need to schedule anything else. Take care!",
        "You're all set! ✨ I'm always here when you need help with appointments or scheduling. See you next time!"
    ]
    return random.choice(goodbyes)

def processing_response() -> str:
    """Generate a processing response."""
    return (
        "Perfect! Let me book that for you right now... ⏳\n\n"
        "**Processing your appointment...**\n"
        "• 📅 Checking calendar availability\n"
        "• ✅ Confirming the time slot\n"
        "• 📧 Creating the calendar event\n"
        "• 🔔 Setting up reminders\n\n"
        "**Just a moment while I get everything set up for you!** ✨"
    )

def slot_selection_confirmation(slot_number: int, slot_details: dict) -> str:
    """Generate a confirmation when user selects a slot."""
    start_time = slot_details.get('start', '')
    end_time = slot_details.get('end', '')
    
    # Format the time nicely
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
        f"**You selected:**\n"
        f"📅 **Slot {slot_number}:** {time_str}\n\n"
        f"**Ready to book this appointment?**\n\n"
        f"**Just say:**\n"
        "• \"**Yes**\" or \"**Book it**\" to confirm\n"
        "• \"**No**\" to pick a different time\n"
        "• \"**Change**\" to modify the details\n\n"
        f"**I'm ready to schedule this for you!** ✨"
    ) 