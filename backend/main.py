"""
FastAPI server for the TailorTalk appointment booking agent.
Provides REST API endpoints for chat interaction and calendar operations.
"""

import os
import json
import time
import uuid
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, push_to_gateway
import logging
from logging.handlers import RotatingFileHandler

from backend.agent.booking_agent import booking_agent, AgentState

# Load environment variables
load_dotenv()

# Configure comprehensive logging
def setup_logging():
    """Setup comprehensive logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(
                'logs/app.log',
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Create specific loggers
    logger = logging.getLogger("tailortalk")
    logger.setLevel(logging.INFO)
    
    # Add file handlers for different log levels
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=5*1024*1024,
        backupCount=3
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(error_handler)
    
    return logger

# Setup logging
logger = setup_logging()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize Redis for session management (optional)
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None

# Prometheus metrics
registry = CollectorRegistry()
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    registry=registry
)
BOOKING_COUNT = Counter(
    'appointments_booked_total',
    'Total appointments booked',
    ['status'],
    registry=registry
)

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)

class ChatResponse(BaseModel):
    response: str
    session_id: str
    booking_confirmed: bool = False
    appointment_details: Optional[Dict] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
    uptime: float

# Create FastAPI app with security middleware
app = FastAPI(
    title="TailorTalk AI Appointment Booking Agent",
    description="A conversational AI agent for booking appointments on Google Calendar",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if os.getenv("ENVIRONMENT") != "production" else [
        "localhost",
        "127.0.0.1",
        "*.streamlit.app",  # Allow Streamlit Cloud apps
        "*.onrender.com"    # Allow Render domains
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "https://localhost:8501",
        "https://*.streamlit.app",  # Allow Streamlit Cloud apps
        "https://*.onrender.com"    # Allow Render domains
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security dependencies
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API token (simplified for demo)."""
    if not credentials:
        if os.getenv("ENVIRONMENT") == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API token required"
            )
        return None
    
    # In production, verify against your token store
    expected_token = os.getenv("API_TOKEN")
    if credentials.credentials != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token"
        )
    
    return credentials.credentials

# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics and add request ID."""
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log incoming request
    logger.info(f"Request {request_id}: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        
        # Record metrics
        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"Request {request_id} completed: {response.status_code} in {duration:.3f}s")
        return response
        
    except Exception as e:
        logger.error(f"Request {request_id} failed: {str(e)}")
        raise

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        uptime=time.time() - app.start_time if hasattr(app, 'start_time') else 0
    )

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(registry)

# Chat endpoint with rate limiting and security
@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute
async def chat(
    chat_request: ChatRequest,
    request: Request,
    token: Optional[str] = Depends(verify_token)
):
    """Main chat endpoint for the booking agent."""
    start_time = time.time()
    
    try:
        # Generate session ID if not provided
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Create agent state
        state = AgentState(
            session_id=session_id,
            user_preferences={}
        )
        
        # Add user message
        state.messages.append({
            "role": "user",
            "content": chat_request.message
        })
        
        # Process with agent
        logger.info(f"Processing message for session {session_id}: {chat_request.message[:100]}...")
        
        result = booking_agent.invoke(state.model_dump())
        state = AgentState(**result)
        
        # Get the last assistant message
        assistant_message = None
        for msg in reversed(state.messages):
            if msg["role"] == "assistant":
                assistant_message = msg["content"]
                break
        
        if not assistant_message:
            assistant_message = "I'm sorry, I couldn't process your request. Please try again."
        
        # Track booking metrics
        if state.booking_confirmed:
            BOOKING_COUNT.labels(status="success").inc()
            logger.info(f"Appointment booked successfully for session {session_id}")
        elif state.error_message:
            BOOKING_COUNT.labels(status="error").inc()
            logger.error(f"Error in session {session_id}: {state.error_message}")
        
        # Store session data in Redis if available
        if redis_client:
            try:
                session_data = {
                    "session_id": session_id,
                    "user_id": chat_request.user_id,
                    "last_activity": datetime.now().isoformat(),
                    "booking_confirmed": state.booking_confirmed,
                    "appointment_details": json.dumps(state.appointment_details)
                }
                redis_client.hset(f"session:{session_id}", mapping=session_data)
                redis_client.expire(f"session:{session_id}", 3600)  # 1 hour TTL
            except Exception as e:
                logger.warning(f"Failed to store session data: {e}")
        
        duration = time.time() - start_time
        logger.info(f"Chat response generated in {duration:.3f}s for session {session_id}")
        
        return ChatResponse(
            response=assistant_message,
            session_id=session_id,
            booking_confirmed=state.booking_confirmed,
            appointment_details=state.appointment_details if state.appointment_details else None,
            error=state.error_message
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        BOOKING_COUNT.labels(status="error").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Calendar availability endpoint
@app.get("/calendar/availability")
@limiter.limit("20/minute")
async def get_availability(
    date: str,
    request: Request,
    token: Optional[str] = Depends(verify_token)
):
    """Get calendar availability for a specific date."""
    try:
        from backend.utils.calendar import GoogleCalendarManager
        
        calendar_manager = GoogleCalendarManager(use_service_account=True)
        if not calendar_manager.authenticate():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Calendar service unavailable"
            )
        
        target_date = datetime.fromisoformat(date)
        available_slots = calendar_manager.get_next_available_slots(target_date, 10)
        
        return {
            "date": date,
            "available_slots": available_slots,
            "total_slots": len(available_slots)
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Error getting availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving availability"
        )

# Session management endpoints
@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    if not redis_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Session storage unavailable"
        )
    
    try:
        session_data = redis_client.hgetall(f"session:{session_id}")
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session_data
        
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving session"
        )

if __name__ == "__main__":
    app.start_time = time.time()
    logger.info("Starting TailorTalk AI Appointment Booking Agent")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") != "production",
        log_level="info"
    ) 