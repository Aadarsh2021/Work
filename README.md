# TailorTalk - AI Appointment Booking Assistant

An intelligent conversational AI agent that helps users book appointments through natural language interaction. Built with FastAPI, LangGraph, and Streamlit.

## Features

- 🤖 Natural language conversation for appointment booking
- 📅 Google Calendar integration for real-time availability checking
- 🎯 Smart time slot suggestions based on user preferences
- 💬 Beautiful chat interface with real-time typing indicators
- 🔒 Secure API with rate limiting and authentication
- 📊 Monitoring and logging capabilities

## Tech Stack

- **Backend**: Python with FastAPI
- **Agent Framework**: LangGraph
- **Frontend**: Streamlit
- **Calendar Integration**: Google Calendar API
- **AI/ML**: LangChain, OpenAI GPT-3.5
- **Monitoring**: Prometheus, Redis (optional)

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tailortalk.git
   cd tailortalk
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_CALENDAR_CREDENTIALS=credentials.json
   USE_SERVICE_ACCOUNT=true
   CALENDAR_ID=your_calendar_id_here
   ENVIRONMENT=development
   API_TOKEN=your_api_token_here
   ```

5. Set up Google Calendar credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select an existing one
   - Enable the Google Calendar API
   - Create credentials (OAuth 2.0 or Service Account)
   - Download the credentials and save as `credentials.json` in the project root

6. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

7. Start the Streamlit frontend:
   ```bash
   cd frontend
   streamlit run app.py
   ```

8. Open your browser and navigate to:
   - Frontend: http://localhost:8501
   - API Documentation: http://localhost:8000/docs

## Usage Examples

The AI agent can handle natural language requests like:

- "Hey, I want to schedule a call for tomorrow afternoon."
- "Do you have any free time this Friday?"
- "Book a meeting between 3-5 PM next week."

## Project Structure

```
tailortalk/
├── backend/
│   ├── agent/
│   │   ├── booking_agent.py
│   │   ├── responses.py
│   │   └── tools.py
│   ├── utils/
│   │   └── calendar.py
│   └── main.py
├── frontend/
│   └── app.py
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-3.5
- LangChain and LangGraph teams
- Streamlit team
- FastAPI team 