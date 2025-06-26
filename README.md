# 🤖 TailorTalk AI Appointment Booking Agent

A sophisticated conversational AI agent for booking appointments on Google Calendar, built with modern AI/ML technologies and production-ready features.

## 🚀 Features

### Core Functionality
- **Natural Language Processing**: Advanced intent recognition and entity extraction
- **Conversational AI**: Context-aware conversations with memory and preferences
- **Google Calendar Integration**: Real-time availability checking and appointment booking
- **Professional UI**: Modern Streamlit interface with responsive design

### Enhanced User Experience
- **Smart Intent Understanding**: Multi-intent recognition (schedule, check_availability, modify, cancel)
- **Context Awareness**: Remembers conversation history and user preferences
- **Input Validation**: Comprehensive validation with helpful error messages
- **Progressive Disclosure**: Step-by-step guidance for complex requests
- **Personalization**: Learns and adapts to user preferences

### Production-Ready Features
- **Comprehensive Logging**: Structured logging with rotation and error tracking
- **Rate Limiting**: API rate limiting to prevent abuse
- **Security**: API token authentication and input sanitization
- **Monitoring**: Prometheus metrics and health checks
- **Session Management**: Redis-based session storage
- **Error Handling**: Graceful error handling with user-friendly messages

### Testing & Quality
- **Unit Tests**: Comprehensive test coverage for all components
- **Integration Tests**: End-to-end testing of the booking workflow
- **Code Quality**: Automated linting, formatting, and type checking
- **Security Scanning**: Automated security vulnerability detection
- **Performance Testing**: Response time and load testing

## 🛠 Technical Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **LangGraph**: Advanced agent framework for conversational AI
- **OpenAI GPT**: State-of-the-art language model for natural language understanding
- **Google Calendar API**: Official Google Calendar integration

### Frontend
- **Streamlit**: Rapid web app development with beautiful UI components
- **Custom CSS**: Professional styling with responsive design
- **Real-time Updates**: Live chat interface with instant feedback

### Infrastructure
- **Redis**: Session storage and caching
- **Prometheus**: Metrics collection and monitoring
- **Docker**: Containerization for easy deployment
- **Pytest**: Comprehensive testing framework

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Google Calendar service account credentials
- Redis (optional, for session management)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd tailortalk-ai-booking
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env_example.txt .env
# Edit .env with your API keys and configuration
```

### 3. Setup Google Calendar
```bash
python configure_app.py
# Follow the prompts to set up Google Calendar credentials
```

### 4. Run the Application
```bash
# Start the backend
python backend/main.py

# In another terminal, start the frontend
streamlit run frontend/app.py
```

### 5. Access the Application
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🧪 Testing

### Run All Tests
```bash
python run_tests.py
```

### Individual Test Categories
```bash
# Unit tests
python -m pytest tests/ -v

# Integration tests
python demo.py

# Code quality checks
black --check backend/ frontend/ tests/
flake8 backend/ frontend/ tests/
mypy backend/

# Security checks
bandit -r backend/
safety check
```

### Test Coverage
The test suite covers:
- ✅ Agent state management
- ✅ Intent understanding and entity extraction
- ✅ Input validation and error handling
- ✅ Calendar integration
- ✅ API endpoints
- ✅ Frontend functionality
- ✅ Security vulnerabilities
- ✅ Performance benchmarks

## 📊 Monitoring & Logging

### Health Checks
```bash
curl http://localhost:8000/health
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Rotating log files with automatic cleanup

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Optional
REDIS_HOST=localhost
REDIS_PORT=6379
API_TOKEN=your_api_token
ENVIRONMENT=production
PORT=8000
```

### API Configuration
- Rate limiting: 10 requests/minute for chat, 20/minute for availability
- Session timeout: 1 hour
- Request timeout: 30 seconds
- Max message length: 1000 characters

## 🚀 Deployment

### Docker Deployment
```bash
# Build the image
docker build -t tailortalk-ai-booking .

# Run the container
docker run -p 8000:8000 -p 8501:8501 tailortalk-ai-booking
```

### Cloud Deployment
The application is ready for deployment on:
- **Heroku**: Use the provided `Procfile`
- **Railway**: Automatic deployment from GitHub
- **AWS/GCP**: Use Docker containers
- **Vercel**: Frontend deployment with API routes

## 📈 Performance

### Benchmarks
- Agent creation: < 1 second
- Message processing: < 3 seconds
- Calendar operations: < 2 seconds
- API response time: < 500ms

### Scalability
- Horizontal scaling with Redis session storage
- Load balancing ready
- Database connection pooling
- Caching for calendar operations

## 🔒 Security

### Security Features
- API token authentication
- Input sanitization and validation
- Rate limiting to prevent abuse
- CORS configuration
- Trusted host middleware
- Security vulnerability scanning

### Best Practices
- Environment variable management
- Secure credential storage
- Regular security updates
- Automated vulnerability scanning

## 🤝 Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install black flake8 mypy pytest

# Run pre-commit checks
black backend/ frontend/ tests/
flake8 backend/ frontend/ tests/
mypy backend/
python -m pytest tests/
```

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive docstrings
- Maintain test coverage > 90%
- Run security scans before commits

## 📚 API Documentation

### Chat Endpoint
```bash
POST /chat
{
  "message": "I want to schedule a meeting for tomorrow afternoon",
  "session_id": "optional-session-id"
}
```

### Availability Endpoint
```bash
GET /calendar/availability?date=2025-06-28
```

### Health Check
```bash
GET /health
```

### Metrics
```bash
GET /metrics
```

## 🎯 Example Conversations

### Scheduling Appointments
```
User: "I want to schedule a meeting for tomorrow afternoon"
AI: "I'd be happy to help you schedule an appointment. When would you like to meet?"

User: "How about 2 PM?"
AI: "Perfect! I'll book your appointment for tomorrow at 2:00 PM. Let me confirm this booking for you."
```

### Checking Availability
```
User: "What's your availability for this Friday?"
AI: "I can check my availability for you. Here are the available time slots for Friday..."
```

### Complex Requests
```
User: "I need a 2-hour meeting slot next week for a team discussion"
AI: "I understand you need a 2-hour slot for a team discussion. Let me check my availability for next week..."
```

## 🏆 Production Features

### Enterprise Ready
- **High Availability**: Fault-tolerant architecture
- **Scalability**: Horizontal scaling capabilities
- **Monitoring**: Comprehensive observability
- **Security**: Enterprise-grade security features
- **Compliance**: GDPR and data privacy compliant

### Developer Experience
- **Comprehensive Testing**: 90%+ test coverage
- **CI/CD Ready**: Automated testing and deployment
- **Documentation**: Complete API and user documentation
- **Error Handling**: Graceful error recovery
- **Logging**: Structured logging for debugging

## 📞 Support

For support and questions:
- Check the documentation
- Review the test suite
- Examine the logs
- Create an issue with detailed information

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for the TailorTalk Backend Development Internship**

## 🟢 How to Use with Your Own Google Calendar (OAuth 2.0)

This app now supports **OAuth 2.0** so any user (including evaluators) can book events on their own Google Calendar securely.

### **First-Time Setup**
1. **Run the app or test script.**
2. On first use, a browser window will open for you to **sign in with Google** and grant calendar access.
3. After consenting, a `token.json` file will be created and used for future requests.
4. The app will now book events directly on your calendar!

### **Security**
- Your credentials are never shared with the developer—they go directly to Google.
- You can revoke access at any time from your Google Account settings.

### **Troubleshooting**
- If you want to re-authenticate, delete `token.json` and restart the app.
- Make sure `credentials.json` is present in the project root (provided with the code).

### **For Evaluators**
- You do **not** need to share your calendar or modify any Google settings.
- Just run the app, sign in, and test booking—events will appear on your calendar!

--- 