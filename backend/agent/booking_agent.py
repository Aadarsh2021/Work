"""
LangGraph-based conversational AI agent for appointment booking.
Handles natural language conversation and coordinates calendar operations.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from functools import lru_cache

from backend.agent.tools import (
    check_calendar_availability,
    suggest_time_slots,
    book_appointment,
    get_next_available_slots,
    parse_date_preference
)

# Import enhanced response templates
from backend.agent.responses import (
    greeting_response,
    general_greeting,
    slot_suggestion,
    booking_confirmation,
    clarification_needed,
    clarification_general,
    no_availability,
    error_response,
    help_response,
    goodbye_response,
    processing_response,
    slot_selection_confirmation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple cache for LLM responses
llm_cache = {}

def get_cached_llm_response(prompt: str, cache_key: str = None):
    """Get cached LLM response or make new request."""
    if cache_key is None:
        cache_key = prompt[:100]  # Use first 100 chars as key
    
    if cache_key in llm_cache:
        return llm_cache[cache_key]
    
    try:
        response = get_llm().invoke([HumanMessage(content=prompt)])
        llm_cache[cache_key] = response.content
        return response.content
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return None

# Initialize OpenAI model lazily
def get_llm():
    """Get the OpenAI LLM instance."""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY"),
        request_timeout=30,  # 30 second timeout
        max_tokens=150,  # Limit response length for faster processing
        streaming=False  # Disable streaming for faster responses
    )

class AgentState(BaseModel):
    """Enhanced state for the booking agent conversation."""
    messages: List[Dict] = Field(default_factory=list)
    current_step: str = Field(default="greeting")
    user_intent: Optional[str] = Field(default=None)
    appointment_details: Dict = Field(default_factory=dict)
    available_slots: List[Dict] = Field(default_factory=list)
    booking_confirmed: bool = Field(default=False)
    error_message: Optional[str] = Field(default=None)
    conversation_context: Dict = Field(default_factory=dict)  # Track conversation context
    user_preferences: Dict = Field(default_factory=dict)  # Store user preferences
    validation_errors: List[str] = Field(default_factory=list)  # Track validation errors
    session_id: Optional[str] = Field(default=None)  # Session tracking
    simple_greeting: bool = Field(default=False)  # Flag for simple greetings
    auto_selected_slot: bool = Field(default=False)  # Flag for auto-selected slots

def create_booking_agent():
    """Create the LangGraph booking agent."""
    
    # Define the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes for different conversation stages
    workflow.add_node("greeting", greeting_node)
    workflow.add_node("understand_intent", understand_intent_node)
    workflow.add_node("collect_details", collect_details_node)
    workflow.add_node("check_availability", check_availability_node)
    workflow.add_node("suggest_slots", suggest_slots_node)
    workflow.add_node("confirm_booking", confirm_booking_node)
    workflow.add_node("book_appointment", book_appointment_node)
    workflow.add_node("handle_error", handle_error_node)
    
    # Define the edges
    workflow.set_entry_point("greeting")
    
    # Simplified routing with error handling
    workflow.add_conditional_edges(
        "greeting",
        lambda state: "handle_error" if state.get('error_message') else ("understand_intent" if len(state.get('messages', [])) >= 2 else "end"),
        {
            "understand_intent": "understand_intent",
            "handle_error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "understand_intent",
        lambda state: "handle_error" if state.get('error_message') else ("end" if state.get('simple_greeting', False) else "collect_details"),
        {
            "collect_details": "collect_details",
            "handle_error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "collect_details",
        lambda state: "handle_error" if state.get('error_message') else ("check_availability" if state.get('appointment_details', {}).get('target_date') else "suggest_slots"),
        {
            "check_availability": "check_availability",
            "suggest_slots": "suggest_slots",
            "handle_error": "handle_error"
        }
    )
    
    workflow.add_conditional_edges(
        "check_availability",
        lambda state: "handle_error" if state.get('error_message') else ("book_appointment" if state.get('auto_selected_slot', False) else ("confirm_booking" if state.get('available_slots') else "end")),
        {
            "confirm_booking": "confirm_booking",
            "book_appointment": "book_appointment",
            "handle_error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "suggest_slots",
        lambda state: "handle_error" if state.get('error_message') else ("confirm_booking" if state.get('available_slots') else "end"),
        {
            "confirm_booking": "confirm_booking",
            "handle_error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "confirm_booking",
        lambda state: "handle_error" if state.get('error_message') else ("book_appointment" if state.get('appointment_details', {}).get('title') else "end"),
        {
            "book_appointment": "book_appointment",
            "handle_error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "book_appointment",
        lambda state: "handle_error" if state.get('error_message') else "end",
        {
            "handle_error": "handle_error",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "handle_error",
        lambda state: "end",
        {
            "end": END
        }
    )
    
    return workflow.compile()

def greeting_node(state: AgentState) -> AgentState:
    """Handle initial greeting and introduction."""
    # Use enhanced greeting response
    greeting_message = general_greeting()
    
    state.messages.append({
        "role": "assistant",
        "content": greeting_message
    })
    
    return state.model_dump()

def extract_entities(text: str) -> Dict[str, Any]:
    """Extract entities from natural language text using LLM."""
    try:
        entity_prompt = f"""Extract from: "{text}"
Return JSON: {{"date": "YYYY-MM-DD", "time": "HH:MM", "duration": minutes, "title": "purpose", "urgency": "High/Medium/Low", "participants": number}}"""
        
        response_content = get_cached_llm_response(entity_prompt, f"entities_{text[:50]}")
        if response_content:
            entities = json.loads(response_content)
            logger.info(f"Extracted entities: {entities}")
            return entities
        return {}
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return {}

def validate_appointment_request(details: Dict) -> List[str]:
    """Validate appointment request details."""
    errors = []
    
    # Date validation
    if 'target_date' in details:
        try:
            target_date = datetime.fromisoformat(details['target_date'])
            if target_date < datetime.now():
                errors.append("Cannot book appointments in the past")
            if target_date > datetime.now() + timedelta(days=365):
                errors.append("Cannot book appointments more than 1 year in advance")
        except:
            errors.append("Invalid date format")
    
    # Time validation
    if 'start_hour' in details:
        hour = details['start_hour']
        if hour < 0 or hour > 23:
            errors.append("Invalid hour (must be 0-23)")
        if hour < 9 or hour > 17:
            errors.append("Appointments only available during business hours (9 AM - 5 PM)")
    
    # Duration validation
    if 'duration' in details:
        duration = details.get('duration', 60)
        if duration < 15 or duration > 480:
            errors.append("Duration must be between 15 minutes and 8 hours")
    
    return errors

def understand_intent_node(state: AgentState) -> AgentState:
    """Enhanced intent understanding with ChatGPT-like conversation flow."""
    if not state.messages:
        return state.model_dump()
    
    # Get the last user message
    last_user_message = None
    for msg in reversed(state.messages):
        if msg["role"] == "user":
            last_user_message = msg["content"]
            break
    
    if not last_user_message:
        return state.model_dump()
    
    # Check for simple greetings first
    simple_greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'howdy']
    if last_user_message.lower().strip() in simple_greetings:
        response_msg = general_greeting()
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
        state.simple_greeting = True
        return state.model_dump()
    
    # Check for help requests
    help_keywords = ['help', 'what can you do', 'how does this work', 'show me examples']
    if any(keyword in last_user_message.lower() for keyword in help_keywords):
        response_msg = help_response()
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
        state.simple_greeting = True
        return state.model_dump()
    
    # Check for goodbye
    goodbye_keywords = ['bye', 'goodbye', 'thanks', 'thank you', 'see you', 'that\'s all']
    if any(keyword in last_user_message.lower() for keyword in goodbye_keywords):
        response_msg = goodbye_response()
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
        state.simple_greeting = True
        return state.model_dump()
    
    # Enhanced intent analysis with context for non-greeting messages
    intent_prompt = f"""Analyze the following user message and determine the user's intent for a calendar assistant. Always respond ONLY with a valid JSON object in this format:
{{
  "intent": "schedule|check_availability|general_inquiry|modify|cancel",
  "confidence": "High|Medium|Low",
  "context_changes": {{}},
  "follow_up_needed": [],
  "entities": {{}}
}}
User Message: "{last_user_message}"
"""

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            response_content = get_cached_llm_response(intent_prompt, f"intent_{last_user_message[:50]}_{attempt}")
            logger.info(f"LLM intent response (attempt {attempt}): {response_content}")
            if response_content and response_content.strip():
                try:
                    intent_analysis = json.loads(response_content)
                    state.user_intent = intent_analysis.get('intent', 'general_inquiry')
                    state.conversation_context.update(intent_analysis.get('context_changes', {}))
                    
                    # Extract entities
                    entities = extract_entities(last_user_message)
                    state.conversation_context.update(entities)
                    
                    # Generate appropriate response based on intent and context
                    if state.user_intent == "schedule":
                        if not state.conversation_context.get('date'):
                            response_msg = (
                                "I'd be happy to help you schedule an appointment! 📅\n\n"
                                "**When would you like to meet?** You can say things like:\n"
                                "• 'tomorrow afternoon'\n"
                                "• 'next Friday morning'\n"
                                "• '3 PM next week'\n"
                                "• 'Monday at 2:30 PM'\n"
                                "• 'any time this week'\n\n"
                                "**What works best for you?** I'll find the perfect slot! 😊"
                            )
                        elif not state.conversation_context.get('time'):
                            response_msg = (
                                f"Great! I see you want to meet on **{state.conversation_context.get('date')}**. "
                                f"Let me check my availability for that day.\n\n"
                                f"**What time works best for you?** You can be specific like '2 PM' or general like 'morning' or 'afternoon'."
                            )
                        else:
                            response_msg = (
                                f"Perfect! I understand you want to meet on **{state.conversation_context.get('date')}** "
                                f"at **{state.conversation_context.get('time')}**.\n\n"
                                f"Let me check my availability and find the best slot for you! 🔍"
                            )
                    elif state.user_intent == "check_availability":
                        response_msg = (
                            "I can definitely check my availability for you! 📋\n\n"
                            "**What date or time period are you interested in?** For example:\n"
                            "• 'tomorrow'\n"
                            "• 'this Friday'\n"
                            "• 'next week'\n"
                            "• 'between 2-4 PM today'\n\n"
                            "Just let me know when you'd like to check!"
                        )
                    elif state.user_intent == "modify":
                        response_msg = (
                            "I can help you modify your appointment! 🔄\n\n"
                            "**What changes would you like to make?** You can:\n"
                            "• Change the date or time\n"
                            "• Update the meeting title\n"
                            "• Adjust the duration\n\n"
                            "What would you like to modify?"
                        )
                    elif state.user_intent == "cancel":
                        response_msg = (
                            "I can help you cancel your appointment! ❌\n\n"
                            "**Which appointment would you like to cancel?** Please let me know:\n"
                            "• The date and time of the appointment\n"
                            "• Or the meeting title\n\n"
                            "I'll help you cancel it right away."
                        )
                    else:
                        # General inquiry - provide helpful guidance
                        response_msg = (
                            "I'm here to help you with all your scheduling needs! 🤝\n\n"
                            "**What would you like to do?**\n\n"
                            "**📅 Book an appointment:**\n"
                            "• \"Schedule a meeting for tomorrow afternoon\"\n"
                            "• \"Book me for next Friday at 2 PM\"\n\n"
                            "**🔍 Check availability:**\n"
                            "• \"What's my availability this week?\"\n"
                            "• \"Show me free slots for Friday\"\n\n"
                            "**💡 Get suggestions:**\n"
                            "• \"Find me a good time next week\"\n"
                            "• \"What's the best slot for a 1-hour meeting?\"\n\n"
                            "**Just tell me what you need, and I'll guide you through it!** 😊"
                        )
                    
                    state.messages.append({
                        "role": "assistant",
                        "content": response_msg
                    })
                    
                    logger.info(f"Intent understood: {state.user_intent}")
                    break
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error on attempt {attempt}: {e}")
                    if attempt == max_retries:
                        # Fallback response
                        response_msg = (
                            "I'd love to help you with that! 🤝\n\n"
                            "**Could you tell me a bit more about what you need?** For example:\n\n"
                            "• **\"I need to schedule a meeting\"** → When would you like to meet?\n"
                            "• **\"Check my calendar\"** → What date or time period?\n"
                            "• **\"Book something\"** → What type of appointment and when?\n\n"
                            "**Just let me know what you need, and I'll make it happen!** ✨"
                        )
                        
                        state.messages.append({
                            "role": "assistant",
                            "content": response_msg
                        })
                    continue
            else:
                if attempt == max_retries:
                    # Fallback response for empty LLM response
                    response_msg = (
                        "I'd love to help you with that! 🤝\n\n"
                        "**Could you tell me a bit more about what you need?** For example:\n\n"
                        "• **\"I need to schedule a meeting\"** → When would you like to meet?\n"
                        "• **\"Check my calendar\"** → What date or time period?\n"
                        "• **\"Book something\"** → What type of appointment and when?\n\n"
                        "**Just let me know what you need, and I'll make it happen!** ✨"
                    )
                    
                    state.messages.append({
                        "role": "assistant",
                        "content": response_msg
                    })
                continue
                
        except Exception as e:
            logger.error(f"Error in intent understanding (attempt {attempt}): {e}")
            if attempt == max_retries:
                # Fallback response
                response_msg = (
                    "I'd love to help you with that! 🤝\n\n"
                    "**Could you tell me a bit more about what you need?** For example:\n\n"
                    "• **\"I need to schedule a meeting\"** → When would you like to meet?\n"
                    "• **\"Check my calendar\"** → What date or time period?\n"
                    "• **\"Book something\"** → What type of appointment and when?\n\n"
                    "**Just let me know what you need, and I'll make it happen!** ✨"
                )
                
                state.messages.append({
                    "role": "assistant",
                    "content": response_msg
                })
            continue
    
    return state.model_dump()

def collect_details_node(state: AgentState) -> AgentState:
    """Collect and parse appointment details from user input."""
    try:
        if not state.messages:
            return state.model_dump()
        
        # Get the last user message
        last_user_message = None
        for msg in reversed(state.messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        if not last_user_message:
            return state.model_dump()
        
        # Parse appointment details using the parse_date_preference tool
        try:
            parsed_info = parse_date_preference(last_user_message)
            
            if parsed_info and 'target_date' in parsed_info:
                # Update appointment details with parsed information
                state.appointment_details.update(parsed_info)
                state.appointment_details['parsed_input'] = last_user_message
                
                # Store user preferences
                if 'time_preference' in parsed_info:
                    state.user_preferences['time_preference'] = parsed_info['time_preference']
                if 'target_date' in parsed_info:
                    state.user_preferences['preferred_date'] = parsed_info['target_date']
                
                # Generate detailed confirmation message
                target_date = parsed_info.get('target_date', 'a date')
                time_pref = parsed_info.get('time_preference', 'a time slot')
                start_hour = parsed_info.get('start_hour', 'TBD')
                
                response_msg = (
                    f"Perfect! I understand you're looking for **{time_pref}** "
                    f"on **{target_date}**.\n\n"
                )
                
                if start_hour != 'TBD':
                    response_msg += f"**Proposed time:** {start_hour}:00\n\n"
                
                response_msg += (
                    "Let me check my availability for you and show you the best options! 🔍\n\n"
                    "I'll find several time slots that work for you, and you can choose the one that fits your schedule best."
                )
                
                # Add helpful suggestions based on context
                if state.conversation_context.get('urgency') == 'High':
                    response_msg += "\n\n💡 **I notice this seems urgent** - I'll prioritize finding you a slot as soon as possible!"
                elif isinstance(state.conversation_context.get('participants'), int) and state.conversation_context.get('participants', 0) > 2:
                    response_msg += f"\n\n💡 **For a meeting with {state.conversation_context.get('participants')} participants**, I'll ensure we have enough time allocated."
                
            else:
                # No specific date found, provide helpful guidance
                response_msg = (
                    "I'd love to help you schedule that appointment! 🤝\n\n"
                    "**Could you please be more specific about the time?** Here are some examples:\n\n"
                    "• **'tomorrow afternoon'** (1 PM - 5 PM)\n"
                    "• **'next Friday morning'** (9 AM - 12 PM)\n"
                    "• **'3 PM next week'** (specific time)\n"
                    "• **'Monday at 2:30 PM'** (specific day and time)\n"
                    "• **'any time this week'** (flexible)\n\n"
                    "**What works best for you?** Just let me know when you'd like to meet!"
                )
            
        except Exception as e:
            logger.error(f"Error parsing date preference: {e}")
            # Fallback response for parsing errors
            response_msg = (
                "I'd love to help you schedule that appointment! 🤝\n\n"
                "**Could you please be more specific about the time?** Here are some examples:\n\n"
                "• **'tomorrow afternoon'** (1 PM - 5 PM)\n"
                "• **'next Friday morning'** (9 AM - 12 PM)\n"
                "• **'3 PM next week'** (specific time)\n"
                "• **'Monday at 2:30 PM'** (specific day and time)\n"
                "• **'any time this week'** (flexible)\n\n"
                "**What works best for you?** Just let me know when you'd like to meet!"
            )
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
        logger.info(f"Collected appointment details: {state.appointment_details}")
        
    except Exception as e:
        logger.error(f"Error collecting details: {e}")
        state.error_message = f"Error collecting details: {str(e)}"
    
    return state.model_dump()

def check_availability_node(state: AgentState) -> AgentState:
    """Check calendar availability based on collected details."""
    try:
        if not state.appointment_details:
            state.error_message = "No appointment details available to check availability"
            return state.model_dump()
        
        target_date = state.appointment_details.get('target_date')
        if not target_date:
            state.error_message = "No target date specified"
            return state.model_dump()
        
        # Check availability for the target date using the calendar manager directly
        try:
            from backend.utils.calendar import GoogleCalendarManager
            calendar_manager = GoogleCalendarManager(use_service_account=True)
            if calendar_manager.authenticate():
                # Parse date without timezone for local date
                target_dt = datetime.fromisoformat(target_date)
                
                # Use suggest_time_slots instead of get_next_available_slots to handle specific times
                # Get the last user message to pass to suggest_time_slots
                last_user_message = None
                for msg in reversed(state.messages):
                    if msg["role"] == "user":
                        last_user_message = msg["content"]
                        break
                
                if last_user_message:
                    available_slots = calendar_manager.suggest_time_slots(last_user_message)
                    
                    # Check if this is a specific time request and auto-select the best slot
                    parsed_preference = parse_date_preference(last_user_message)
                    is_specific_time = "specific time" in parsed_preference.get('time_preference', '')
                    
                    if is_specific_time and available_slots:
                        # Auto-select the first (best) slot for specific time requests
                        best_slot = available_slots[0]
                        start_time_str = best_slot['start']
                        end_time_str = best_slot['end']
                        
                        # Parse the selected time
                        start_dt = datetime.fromisoformat(start_time_str.replace('Z', ''))
                        end_dt = datetime.fromisoformat(end_time_str.replace('Z', ''))
                        
                        # Format for display
                        time_str = start_dt.strftime('%I:%M %p')
                        duration_minutes = best_slot.get('duration_minutes', 60)
                        
                        # Create slot info
                        slot_info = {
                            'number': 1,
                            'time': time_str,
                            'duration': f"{duration_minutes} minutes",
                            'start': start_dt.strftime('%Y-%m-%d %H:%M'),
                            'end': end_dt.strftime('%Y-%m-%d %H:%M')
                        }
                        
                        # Update appointment details with the selected slot
                        state.appointment_details.update({
                            'title': f"Appointment - {state.appointment_details.get('parsed_input', 'Meeting')}",
                            'start_time': start_time_str,
                            'end_time': end_time_str,
                            'start_hour': start_dt.hour,
                            'selected_slot': slot_info
                        })
                        
                        # Set available slots to just the selected one
                        state.available_slots = [slot_info]
                        
                        # Create confirmation message for auto-selected slot
                        date_str = target_dt.strftime('%A, %B %d, %Y')
                        response_msg = (
                            f"Perfect! I found the best available slot for your requested time of **{parsed_preference['time_preference']}** on **{date_str}**:\n\n"
                            f"📅 **Selected:** {time_str} ({duration_minutes} minutes)\n\n"
                            f"**Ready to book this appointment?**\n\n"
                            f"**Just say:**\n"
                            f"• \"**Yes**\" or \"**Book it**\" to confirm\n"
                            f"• \"**No**\" to see other options\n"
                            f"• \"**Change**\" to modify the time\n\n"
                            f"**I'm ready to schedule this for you!** ✨"
                        )
                        state.auto_selected_slot = True
                    else:
                        # For general requests, show all available slots
                        if available_slots:
                            # Format the slots for display
                            slots_info = []
                            for i, slot in enumerate(available_slots[:8], 1):  # Show up to 8 slots
                                try:
                                    # Handle timezone-aware datetime strings
                                    start_str = slot['start']
                                    end_str = slot['end']
                                    
                                    # Remove timezone info if present for parsing
                                    if start_str.endswith('Z'):
                                        start_str = start_str[:-1]
                                    if end_str.endswith('Z'):
                                        end_str = end_str[:-1]
                                    
                                    start_time = datetime.fromisoformat(start_str)
                                    end_time = datetime.fromisoformat(end_str)
                                    
                                    # Format time in a user-friendly way
                                    time_str = start_time.strftime('%I:%M %p')  # e.g., "2:30 PM"
                                    duration_minutes = slot.get('duration_minutes', 60)
                                    
                                    slots_info.append({
                                        'number': i,
                                        'time': time_str,
                                        'duration': f"{duration_minutes} minutes",
                                        'start': start_time.strftime('%Y-%m-%d %H:%M'),
                                        'end': end_time.strftime('%Y-%m-%d %H:%M')
                                    })
                                except Exception as e:
                                    logger.warning(f"Error formatting slot {i}: {e}")
                                    continue
                            
                            if slots_info:
                                state.available_slots = slots_info
                                
                                # Create a user-friendly response
                                date_str = target_dt.strftime('%A, %B %d, %Y')  # e.g., "Friday, June 27, 2025"
                                response_msg = f"Great! Here are the available time slots for **{date_str}**: 📅\n\n"
                                
                                for slot in slots_info:
                                    response_msg += f"**{slot['number']}.** {slot['time']} ({slot['duration']})\n"
                                
                                response_msg += "\n**How to choose:**\n"
                                response_msg += "• Just tell me the **number** (like '1' or 'slot 3')\n"
                                response_msg += "• Or tell me the **time** (like '2:30 PM')\n"
                                response_msg += "• Or say **'yes'** to confirm the first available slot\n\n"
                                response_msg += "**Which time works best for you?** 🤔"
                                
                                # Add helpful suggestions
                                if len(slots_info) >= 3:
                                    response_msg += f"\n\n💡 **Recommendation**: I recommend slot **{slots_info[0]['number']}** ({slots_info[0]['time']}) as it's early in the day and gives you plenty of time for other activities!"
                                elif len(slots_info) == 2:
                                    response_msg += f"\n\n💡 **Quick tip**: Both slots look great! Slot **{slots_info[0]['number']}** is earlier, and slot **{slots_info[1]['number']}** is later in the day."
                                else:
                                    response_msg += f"\n\n💡 **Perfect timing**: This is the only available slot for that day, so it's a great choice!"
                            else:
                                state.available_slots = []
                                response_msg = (
                                    f"I couldn't find any available slots for **{target_dt.strftime('%A, %B %d, %Y')}**. 😔\n\n"
                                    f"**Don't worry!** Here are some alternatives:\n"
                                    f"• Try a **different date** (like tomorrow or next week)\n"
                                    f"• Ask for **morning slots** instead of afternoon\n"
                                    f"• Request a **shorter meeting** (30 minutes instead of 1 hour)\n\n"
                                    f"**What would you like to try?** I'm here to help find a time that works for you! 🤝"
                                )
                        else:
                            state.available_slots = []
                            response_msg = (
                                f"I couldn't find available slots for **{target_dt.strftime('%A, %B %d, %Y')}**. 😔\n\n"
                                f"**Let's try something else:**\n"
                                f"• A **different day** this week\n"
                                f"• **Morning** instead of afternoon\n"
                                f"• **Next week** if you're flexible\n\n"
                                f"**What works better for you?** Just let me know! 📅"
                            )
                else:
                    # Fallback to general availability if no user message
                    available_slots = calendar_manager.get_next_available_slots(target_dt, 8)
                    
                    if available_slots:
                        # Format the slots for display
                        slots_info = []
                        for i, slot in enumerate(available_slots[:8], 1):  # Show up to 8 slots
                            try:
                                # Handle timezone-aware datetime strings
                                start_str = slot['start']
                                end_str = slot['end']
                                
                                # Remove timezone info if present for parsing
                                if start_str.endswith('Z'):
                                    start_str = start_str[:-1]
                                if end_str.endswith('Z'):
                                    end_str = end_str[:-1]
                                
                                start_time = datetime.fromisoformat(start_str)
                                end_time = datetime.fromisoformat(end_str)
                                
                                # Format time in a user-friendly way
                                time_str = start_time.strftime('%I:%M %p')  # e.g., "2:30 PM"
                                duration_minutes = slot.get('duration_minutes', 60)
                                
                                slots_info.append({
                                    'number': i,
                                    'time': time_str,
                                    'duration': f"{duration_minutes} minutes",
                                    'start': start_time.strftime('%Y-%m-%d %H:%M'),
                                    'end': end_time.strftime('%Y-%m-%d %H:%M')
                                })
                            except Exception as e:
                                logger.warning(f"Error formatting slot {i}: {e}")
                                continue
                        
                        if slots_info:
                            state.available_slots = slots_info
                            
                            # Create a user-friendly response
                            date_str = target_dt.strftime('%A, %B %d, %Y')  # e.g., "Friday, June 27, 2025"
                            response_msg = f"Great! Here are the available time slots for **{date_str}**: 📅\n\n"
                            
                            for slot in slots_info:
                                response_msg += f"**{slot['number']}.** {slot['time']} ({slot['duration']})\n"
                            
                            response_msg += "\n**How to choose:**\n"
                            response_msg += "• Just tell me the **number** (like '1' or 'slot 3')\n"
                            response_msg += "• Or tell me the **time** (like '2:30 PM')\n"
                            response_msg += "• Or say **'yes'** to confirm the first available slot\n\n"
                            response_msg += "**Which time works best for you?** 🤔"
                            
                            # Add helpful suggestions
                            if len(slots_info) >= 3:
                                response_msg += f"\n\n💡 **Recommendation**: I recommend slot **{slots_info[0]['number']}** ({slots_info[0]['time']}) as it's early in the day and gives you plenty of time for other activities!"
                            elif len(slots_info) == 2:
                                response_msg += f"\n\n💡 **Quick tip**: Both slots look great! Slot **{slots_info[0]['number']}** is earlier, and slot **{slots_info[1]['number']}** is later in the day."
                            else:
                                response_msg += f"\n\n💡 **Perfect timing**: This is the only available slot for that day, so it's a great choice!"
                        else:
                            state.available_slots = []
                            response_msg = (
                                f"I couldn't find any available slots for **{target_dt.strftime('%A, %B %d, %Y')}**. 😔\n\n"
                                f"**Don't worry!** Here are some alternatives:\n"
                                f"• Try a **different date** (like tomorrow or next week)\n"
                                f"• Ask for **morning slots** instead of afternoon\n"
                                f"• Request a **shorter meeting** (30 minutes instead of 1 hour)\n\n"
                                f"**What would you like to try?** I'm here to help find a time that works for you! 🤝"
                            )
                    else:
                        state.available_slots = []
                        response_msg = (
                            f"I couldn't find available slots for **{target_dt.strftime('%A, %B %d, %Y')}**. 😔\n\n"
                            f"**Let's try something else:**\n"
                            f"• A **different day** this week\n"
                            f"• **Morning** instead of afternoon\n"
                            f"• **Next week** if you're flexible\n\n"
                            f"**What works better for you?** Just let me know! 📅"
                        )
            else:
                state.available_slots = []
                response_msg = (
                    "I'm having trouble accessing the calendar right now. 😅\n\n"
                    "**This usually happens when:**\n"
                    "• The calendar is temporarily unavailable\n"
                    "• There's a brief connection issue\n\n"
                    "**Please try again in a few minutes** - I'll be here to help! 🤝"
                )
        except Exception as e:
            logger.error(f"Calendar error: {e}")
            state.available_slots = []
            response_msg = (
                "I couldn't check availability right now due to a technical issue. 😔\n\n"
                "**Don't worry!** This is usually temporary. You can:\n"
                "• **Try again in a few minutes**\n"
                "• **Contact support** if the issue persists\n"
                "• **Send me a message** and I'll help you when the system is back up\n\n"
                "**I apologize for the inconvenience!** 🙏"
            )
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
    except Exception as e:
        logger.error(f"Error in check_availability_node: {e}")
        state.error_message = f"Error checking availability: {str(e)}"
    
    return state.model_dump()

def suggest_slots_node(state: AgentState) -> AgentState:
    """Suggest time slots based on user preferences."""
    try:
        if not state.messages:
            return state.model_dump()
        
        # Get the last user message
        last_user_message = None
        for msg in reversed(state.messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        if not last_user_message:
            return state.model_dump()
        
        # Suggest time slots based on user preference using calendar manager directly
        try:
            from backend.utils.calendar import GoogleCalendarManager
            calendar_manager = GoogleCalendarManager(use_service_account=True)
            if calendar_manager.authenticate():
                suggested_slots = calendar_manager.suggest_time_slots(last_user_message)
                
                if suggested_slots:
                    # Format the slots for display
                    slots_info = []
                    for slot in suggested_slots[:5]:  # Limit to 5 suggestions
                        start_time = datetime.fromisoformat(slot['start'])
                        end_time = datetime.fromisoformat(slot['end'])
                        slots_info.append({
                            'start': start_time.strftime('%Y-%m-%d %H:%M'),
                            'end': end_time.strftime('%Y-%m-%d %H:%M'),
                            'duration': f"{slot['duration_minutes']} minutes"
                        })
                    state.available_slots = slots_info
                    
                    # Use enhanced slot suggestion response
                    date_str = state.appointment_details.get('target_date', '')
                    if date_str:
                        try:
                            date_obj = datetime.fromisoformat(date_str)
                            date_str = date_obj.strftime('%A, %B %d, %Y')
                        except:
                            pass
                    
                    response_msg = slot_suggestion(slots_info, date_str)
                else:
                    state.available_slots = []
                    response_msg = no_availability()
            else:
                state.available_slots = []
                response_msg = error_response("calendar")
        except Exception as e:
            state.available_slots = []
            response_msg = error_response("general")
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
    except Exception as e:
        state.error_message = f"Error suggesting slots: {str(e)}"
    
    return state.model_dump()

def confirm_booking_node(state: AgentState) -> AgentState:
    """Confirm booking details with user."""
    try:
        if not state.messages:
            return state.model_dump()
        
        # Get the last user message
        last_user_message = None
        for msg in reversed(state.messages):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        if not last_user_message:
            return state.model_dump()
        
        # Check if user is selecting a slot from the numbered list
        slot_selected = None
        if state.available_slots:
            # Check for slot number selection (e.g., "1", "2", "slot 3")
            import re
            slot_match = re.search(r'(?:slot\s+)?(\d+)', last_user_message.lower())
            if slot_match:
                slot_num = int(slot_match.group(1))
                if 1 <= slot_num <= len(state.available_slots):
                    slot_selected = state.available_slots[slot_num - 1]
            
            # Check for time selection (e.g., "2:30 PM", "14:30")
            if not slot_selected:
                for slot in state.available_slots:
                    if slot.get('time', '').lower() in last_user_message.lower():
                        slot_selected = slot
                        break
        
        # Check if user is confirming the booking
        confirmation_keywords = ["yes", "confirm", "book", "schedule", "okay", "sure", "perfect", "that works"]
        is_confirming = any(keyword in last_user_message.lower() for keyword in confirmation_keywords)
        
        if slot_selected:
            # User selected a specific slot
            target_date = state.appointment_details.get('target_date')
            start_time_str = slot_selected['start']
            end_time_str = slot_selected['end']
            
            # Parse the selected time
            start_dt = datetime.fromisoformat(start_time_str)
            end_dt = datetime.fromisoformat(end_time_str)
            
            # Update appointment details
            state.appointment_details.update({
                'title': f"Appointment - {state.appointment_details.get('parsed_input', 'Meeting')}",
                'start_time': start_time_str,
                'end_time': end_time_str,
                'start_hour': start_dt.hour,
                'selected_slot': slot_selected
            })
            
            # Use enhanced slot selection confirmation
            response_msg = slot_selection_confirmation(
                slot_num if 'slot_num' in locals() else 1, 
                slot_selected
            )
            
        elif is_confirming:
            # User is confirming the booking
            if state.appointment_details.get('start_time') and state.appointment_details.get('end_time'):
                response_msg = processing_response()
            else:
                response_msg = clarification_needed()
        else:
            # User didn't select a slot or confirm - ask for clarification
            if state.available_slots:
                response_msg = slot_suggestion(state.available_slots)
            else:
                response_msg = clarification_general()
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
    except Exception as e:
        logger.error(f"Error in confirm_booking_node: {e}")
        state.error_message = f"Error confirming booking: {str(e)}"
    
    return state.model_dump()

def book_appointment_node(state: AgentState) -> AgentState:
    """Actually book the appointment in the calendar."""
    try:
        if not state.appointment_details:
            state.error_message = "No appointment details available for booking"
            return state.model_dump()
        
        title = state.appointment_details.get('title', 'Appointment')
        start_time = state.appointment_details.get('start_time')
        end_time = state.appointment_details.get('end_time')
        description = state.appointment_details.get('description', '')
        
        if not all([title, start_time, end_time]):
            state.error_message = "Missing required appointment details"
            return state.model_dump()
        
        # Book the appointment using calendar manager directly
        max_booking_attempts = 2
        for attempt in range(max_booking_attempts + 1):
            try:
                from backend.utils.calendar import GoogleCalendarManager
                calendar_manager = GoogleCalendarManager(use_service_account=True)
                if calendar_manager.authenticate():
                    start_dt = datetime.fromisoformat(start_time)
                    end_dt = datetime.fromisoformat(end_time)
                    
                    # Check if slot is still available before booking
                    if attempt > 0:
                        # On retry, check if the slot is still available
                        available_slots = calendar_manager.get_next_available_slots(start_dt.date(), 1)
                        slot_still_available = False
                        for slot in available_slots:
                            slot_start = datetime.fromisoformat(slot['start'].replace('Z', ''))
                            if abs((slot_start - start_dt).total_seconds()) < 300:  # Within 5 minutes
                                slot_still_available = True
                                break
                        
                        if not slot_still_available:
                            response_msg = no_availability()
                            state.messages.append({
                                "role": "assistant",
                                "content": response_msg
                            })
                            return state.model_dump()
                    
                    result = calendar_manager.book_appointment(title, start_dt, end_dt, description)
                    
                    if result['success']:
                        state.booking_confirmed = True
                        
                        # Use enhanced booking confirmation response
                        booking_details = {
                            'date': start_dt.strftime('%A, %B %d, %Y'),
                            'start_time': start_dt.strftime('%I:%M %p'),
                            'end_time': end_dt.strftime('%I:%M %p'),
                            'duration': int((end_dt - start_dt).total_seconds() / 60),
                            'event_id': result['event_id'],
                            'calendar_link': result.get('event_link', '')
                        }
                        
                        response_msg = booking_confirmation(booking_details)
                        
                        logger.info(f"Appointment booked successfully: {result['event_id']}")
                        break
                    else:
                        if attempt < max_booking_attempts:
                            logger.warning(f"Booking attempt {attempt + 1} failed: {result['error']}")
                            continue
                        else:
                            response_msg = error_response("booking")
                else:
                    if attempt < max_booking_attempts:
                        logger.warning(f"Calendar authentication failed on attempt {attempt + 1}")
                        continue
                    else:
                        response_msg = error_response("calendar")
            except Exception as e:
                logger.error(f"Booking error on attempt {attempt + 1}: {e}")
                if attempt < max_booking_attempts:
                    continue
                else:
                    response_msg = error_response("general")
        
        state.messages.append({
            "role": "assistant",
            "content": response_msg
        })
        
    except Exception as e:
        logger.error(f"Error in book_appointment_node: {e}")
        state.error_message = f"Error booking appointment: {str(e)}"
    
    return state.model_dump()

def handle_error_node(state: AgentState) -> AgentState:
    """Handle errors gracefully."""
    error_msg = state.error_message or "An unexpected error occurred"
    
    # Provide more helpful error messages based on the type of error
    if "intent" in error_msg.lower():
        response_msg = clarification_general()
    elif "calendar" in error_msg.lower() or "availability" in error_msg.lower():
        response_msg = error_response("calendar")
    elif "booking" in error_msg.lower():
        response_msg = error_response("booking")
    else:
        response_msg = error_response("general")
    
    state.messages.append({
        "role": "assistant",
        "content": response_msg
    })
    
    return state.model_dump()

# Create the agent instance
booking_agent = create_booking_agent() 