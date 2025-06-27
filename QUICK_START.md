# TailorTalk - Quick Start Guide

## 🚀 Live Demo
- **Frontend**: https://tailortalk-frontend.streamlit.app/
- **Backend**: https://tailortalk-backend-em9b.onrender.com

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.10+
- OpenAI API key
- Google Calendar credentials (optional for full functionality)

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd tailortalk
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env_example.txt .env

# Edit .env with your API keys
# Required: OPENAI_API_KEY
# Optional: Google Calendar credentials for full functionality
```

### 3. Run the Application

#### Option A: Run Both Services
```bash
# Terminal 1: Start backend
python backend/main.py

# Terminal 2: Start frontend
streamlit run frontend/app.py
```

#### Option B: Test System
```bash
# Run comprehensive system test
python test_system.py
```

### 4. Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🧪 Testing the Application

### Example Conversations to Try:
1. "Hello, I'd like to schedule a meeting"
2. "Do you have any free time tomorrow afternoon?"
3. "Book a call for next Friday between 2-4 PM"
4. "What's my schedule look like this week?"

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I want to schedule a meeting"}'
```

## 📁 Project Structure
```
tailortalk/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── agent/               # LangGraph agent
│   └── utils/               # Calendar utilities
├── frontend/
│   └── app.py              # Streamlit interface
├── requirements.txt         # Dependencies
├── test_system.py          # System tests
└── README.md               # Full documentation
```

## 🚀 Deployment

### Backend (Render)
- Connected to GitHub repository
- Auto-deploys on push to main branch
- Environment variables configured in Render dashboard

### Frontend (Streamlit Cloud)
- Connected to GitHub repository
- Auto-deploys on push to main branch
- Streamlit secrets configured for API keys

## 🆘 Troubleshooting

### Common Issues:
1. **Import Errors**: Ensure all dependencies are installed
2. **API Key Issues**: Check your .env file configuration
3. **Port Conflicts**: Change ports in the respective config files
4. **Calendar Issues**: Google Calendar credentials required for full functionality

### Support:
- Check the logs in the `logs/` directory
- Run `python test_system.py` for diagnostics
- Review the full README.md for detailed documentation 