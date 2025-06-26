"""
Streamlit frontend for the TailorTalk appointment booking agent.
Provides a beautiful chat interface for natural language appointment booking.
"""

import streamlit as st
import requests
import json
from datetime import datetime
import time
from typing import Dict, List, Optional
import uuid
import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://tailortalk-backend-em9b.onrender.com")
API_TOKEN = os.getenv("API_TOKEN", st.secrets.get("API_TOKEN", ""))  # Get from environment or Streamlit secrets

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "is_typing" not in st.session_state:
    st.session_state.is_typing = False

# Page configuration
st.set_page_config(
    page_title="TailorTalk AI - Appointment Booking Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-like styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Chat container */
    .chat-container {
        background: rgba(102, 126, 234, 0.15);
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        margin: 20px 0;
    }
    
    /* Message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        animation: slideInRight 0.3s ease-out;
    }
    
    .assistant-message {
        background: #f8f9fa;
        color: #333;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);
        border-left: 4px solid #667eea;
        animation: slideInLeft 0.3s ease-out;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e0e0e0;
        padding: 15px 20px;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Animations */
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: flex;
        align-items: center;
        padding: 15px 20px;
        background: #f8f9fa;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
    }
    
    .typing-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #667eea;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dot:nth-child(1) { animation-delay: -0.32s; }
    .typing-dot:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Header styling */
    .header {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 20px;
        color: white;
    }
    
    .header h1 {
        margin: 0;
        font-size: 2.5em;
        font-weight: 700;
    }
    
    .header p {
        margin: 10px 0 0 0;
        font-size: 1.1em;
        opacity: 0.9;
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
        vertical-align: middle;
    }
    
    .status-online {
        background: #28a745;
        animation: pulse-glow 2s infinite;
        box-shadow: 0 0 8px 3px rgba(40, 167, 69, 0.6), 0 0 15px rgba(40, 167, 69, 0.4);
        transition: box-shadow 0.3s ease-in-out;
    }

    
    .status-offline {
        background: #dc3545;
        box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.3);
    }
    
    @keyframes pulse {
        0% { 
            opacity: 1; 
            box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.3);
        }
        50% { 
            opacity: 0.7; 
            box-shadow: 0 0 0 4px rgba(40, 167, 69, 0.1);
        }
        100% { 
            opacity: 1; 
            box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.3);
        }
    }
    
    /* Remove any default margins/padding that might cause lines */
    .stMarkdown {
        margin: 0;
        padding: 0;
    }
    
    .stMarkdown > div {
        margin: 0;
        padding: 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health():
    """Check if the backend API is healthy."""
    try:
        headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
        response = requests.get(f"{API_BASE_URL}/health", headers=headers, timeout=5)
        st.session_state.last_health_check = {
            "status": response.status_code == 200,
            "timestamp": datetime.now().isoformat(),
            "response": response.json() if response.status_code == 200 else None
        }
        return response.status_code == 200
    except Exception as e:
        st.session_state.last_health_check = {
            "status": False,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
        return False

def send_message(message):
    """Send a message to the backend API, including session_id."""
    try:
        headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json={
                "message": message,
                "session_id": st.session_state.session_id
            },
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
            return {
                "response": f"Sorry, I encountered an error (HTTP {response.status_code}). Please try again.",
                "error": response.text,
                "session_id": st.session_state.session_id
            }
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return {
            "response": "Sorry, I couldn't connect to the backend. Please try again.",
            "error": str(e),
            "session_id": st.session_state.session_id
        }

def format_booking_details(details):
    if not details:
        return ""
    lines = []
    if "title" in details:
        lines.append(f"<b>Title:</b> {details['title']}")
    if "start" in details:
        lines.append(f"<b>Start:</b> {details['start']}")
    if "end" in details:
        lines.append(f"<b>End:</b> {details['end']}")
    if "location" in details:
        lines.append(f"<b>Location:</b> {details['location']}")
    if "link" in details:
        lines.append(f'<b>Link:</b> <a href="{details["link"]}" target="_blank">Open in Calendar</a>')
    return "<br>".join(lines)

def format_message(content, role, booking_confirmed=False, appointment_details=None, error=None):
    if role == "user":
        return f'<div class="user-message">{content}</div>'
    else:
        extra = ""
        if booking_confirmed and appointment_details:
            extra = f'<div style="margin-top:8px; padding:10px; background:#e6ffe6; border-radius:10px; border-left:4px solid #28a745;">✅ <b>Booking Confirmed!</b><br>{format_booking_details(appointment_details)}</div>'
        elif appointment_details:
            extra = f'<div style="margin-top:8px; padding:10px; background:#f0f4ff; border-radius:10px; border-left:4px solid #667eea;">📅 <b>Appointment Details:</b><br>{format_booking_details(appointment_details)}</div>'
        if error:
            extra += f'<div style="margin-top:8px; padding:10px; background:#fff0f0; border-radius:10px; border-left:4px solid #dc3545; color:#dc3545;">❌ <b>Error:</b> {error}</div>'
        return f'<div class="assistant-message">{content}{extra}</div>'

def show_typing_indicator():
    """Show typing indicator."""
    return '''
    <div class="typing-indicator">
        <div class="typing-dots">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
        <span style="margin-left: 10px; color: #666;">AI is thinking...</span>
    </div>
    '''

def handle_quick_action(action: str):
    """Handle a quick action button click."""
    try:
        # Add the action to messages
        st.session_state.messages.append({"role": "user", "content": action})
        
        # Show typing indicator
        st.session_state.is_typing = True
        
        # Send to backend
        response = send_message(action)
        
        # Hide typing indicator
        st.session_state.is_typing = False
        
        if "error" not in response or response.get("error") is None:
            # Add AI response
            st.session_state.messages.append({
                "role": "assistant",
                "content": response.get("response", "I'm sorry, I couldn't process your request."),
                "booking_confirmed": response.get("booking_confirmed", False),
                "appointment_details": response.get("appointment_details"),
                "error": response.get("error")
            })
        else:
            # Add error message
            error_msg = f"Sorry, I'm having trouble connecting right now. Please try again in a moment. ({response['error']})"
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "error": response["error"]
            })
    except Exception as e:
        st.error(f"Error processing quick action: {str(e)}")

# Main app
def main():
    # Header
    st.markdown("""
    <div class="header">
        <h1>TailorTalk AI - Appointment Booking Assistant</h1>
        <p>Your intelligent scheduling companion</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status indicator
    api_healthy = check_api_health()
    status_color = "status-online" if api_healthy else "status-offline"
    status_text = "Online" if api_healthy else "Offline"
    status_bg_color = "#28a745" if api_healthy else "#dc3545"
    
    st.markdown(f"""
    <div style="
        text-align: center; 
        margin: 0 0 20px 0; 
        padding: 8px 16px; 
        background: rgba(255, 255, 255, 0.15); 
        border-radius: 20px; 
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        display: inline-block;
        position: relative;
        left: 50%;
        transform: translateX(-50%);
    ">
        <span style="
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
            vertical-align: middle;
            background: {status_bg_color};
            box-shadow: 0 0 0 2px rgba(40, 167, 69, 0.3);
        "></span>
        <span style="
            color: {status_bg_color}; 
            font-weight: 600; 
            font-size: 13px;
            vertical-align: middle;
        ">
            {status_text}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    if st.session_state.messages:
        # Display chat messages
        for message in st.session_state.messages:
            if message["role"] == "assistant":
                st.markdown(
                    format_message(
                        message["content"],
                        "assistant",
                        booking_confirmed=message.get("booking_confirmed", False),
                        appointment_details=message.get("appointment_details"),
                        error=message.get("error")
                    ),
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    format_message(message["content"], "user"),
                    unsafe_allow_html=True
                )
    else:
        st.markdown(
            '<div style="color:#f8f9fa  ; text-align:center; padding:32px 0; font-size:1.1em;">💬 Start the conversation!<br>Type your message below to begin.</div>',
            unsafe_allow_html=True
        )
    
    # Show typing indicator if AI is thinking
    if st.session_state.is_typing:
        st.markdown(show_typing_indicator(), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    st.markdown("""
    <div style="margin-top: 20px;">
    """, unsafe_allow_html=True)
    
    # Create a form for better UX
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Type your message here...",
                key="user_input",
                placeholder="e.g., 'Schedule a meeting for tomorrow afternoon'",
                label_visibility="collapsed"
            )
        
        with col2:
            submit_button = st.form_submit_button(
                "Send",
                use_container_width=True
            )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Handle form submission
    if submit_button and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Show typing indicator
        st.session_state.is_typing = True
        st.rerun()
    
    # Process AI response if needed
    if st.session_state.is_typing and st.session_state.messages:
        # Get the last user message
        last_message = st.session_state.messages[-1]["content"]
        
        # Send to API
        response = send_message(last_message)
        
        # Hide typing indicator
        st.session_state.is_typing = False
        
        if "error" not in response or response.get("error") is None:
            # Add AI response
            ai_message = response.get("response", "I'm sorry, I couldn't process your request.")
            st.session_state.messages.append({
                "role": "assistant",
                "content": ai_message,
                "booking_confirmed": response.get("booking_confirmed", False),
                "appointment_details": response.get("appointment_details"),
                "error": response.get("error")
            })
        else:
            # Add error message
            error_msg = f"Sorry, I'm having trouble connecting right now. Please try again in a moment. ({response['error']})"
            st.session_state.messages.append({
                "role": "assistant",
                "content": error_msg,
                "error": response["error"]
            })
        
        st.rerun()
    
    # Sidebar with controls
    with st.sidebar:
        st.markdown("### 🎛️ Controls")
        
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 💡 Quick Actions")
        
        quick_actions = [
            "Schedule a meeting for tomorrow afternoon",
            "What's my availability this week?",
            "Book me for next Friday at 2 PM",
            "Find me a good time next week"
        ]
        
        for action in quick_actions:
            if st.button(action, key=f"quick_{action[:20]}", use_container_width=True):
                handle_quick_action(action)
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Info")
        st.markdown(f"**Messages:** {len(st.session_state.messages)}")
        st.markdown(f"**Status:** {'🟢 Online' if api_healthy else '🔴 Offline'}")
        st.markdown(f"**API URL:** `{API_BASE_URL}`")
        
        if not api_healthy:
            st.error("⚠️ Backend is offline. Please check the backend server.")
        
        # Debug section
        with st.expander("Debug Information"):
            st.write("Backend URL:", API_BASE_URL)
            st.write("Session ID:", st.session_state.session_id)
            st.write("API Token configured:", bool(API_TOKEN))
            
            if "last_health_check" in st.session_state:
                with st.expander("Health Check Details"):
                    st.write(st.session_state.last_health_check)

if __name__ == "__main__":
    main() 