# TailorTalk AI Appointment Booking Agent - Deployment Guide

This guide provides comprehensive instructions for deploying the TailorTalk AI Appointment Booking Agent in various environments.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring and Logging](#monitoring-and-logging)
7. [Security Considerations](#security-considerations)

## Local Development Setup

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tailortalk-appointment-agent
   ```

2. **Run setup script**
   ```bash
   python setup.py
   ```

3. **Configure environment**
   ```bash
   # Copy environment template
   cp env_example.txt .env
   
   # Edit .env file with your API keys
   nano .env
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start the application**
   ```bash
   # Terminal 1: Start backend
   python backend/main.py
   
   # Terminal 2: Start frontend
   streamlit run frontend/app.py
   ```

6. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Production Deployment

### Using Gunicorn (Recommended)

1. **Install Gunicorn**
   ```bash
   pip install gunicorn
   ```

2. **Create Gunicorn configuration**
   ```bash
   # gunicorn.conf.py
   bind = "0.0.0.0:8000"
   workers = 4
   worker_class = "uvicorn.workers.UvicornWorker"
   timeout = 120
   keepalive = 2
   ```

3. **Start with Gunicorn**
   ```bash
   gunicorn backend.main:app -c gunicorn.conf.py
   ```

### Using Systemd Service

1. **Create service file**
   ```bash
   sudo nano /etc/systemd/system/tailortalk-backend.service
   ```

2. **Service configuration**
   ```ini
   [Unit]
   Description=TailorTalk Backend API
   After=network.target

   [Service]
   Type=exec
   User=tailortalk
   WorkingDirectory=/opt/tailortalk
   Environment=PATH=/opt/tailortalk/venv/bin
   ExecStart=/opt/tailortalk/venv/bin/gunicorn backend.main:app -c gunicorn.conf.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**
   ```bash
   sudo systemctl enable tailortalk-backend
   sudo systemctl start tailortalk-backend
   ```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose ports
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "backend/main.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
    volumes:
      - ./credentials.json:/app/credentials.json
    restart: unless-stopped

  frontend:
    build: .
    ports:
      - "8501:8501"
    environment:
      - API_BASE_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS Cluster**
   ```bash
   aws ecs create-cluster --cluster-name tailortalk-cluster
   ```

2. **Create Task Definition**
   ```json
   {
     "family": "tailortalk-backend",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "tailortalk-backend",
         "image": "your-account.dkr.ecr.region.amazonaws.com/tailortalk:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "OPENAI_API_KEY",
             "value": "your-openai-key"
           }
         ]
       }
     ]
   }
   ```

3. **Deploy to ECS**
   ```bash
   aws ecs create-service \
     --cluster tailortalk-cluster \
     --service-name tailortalk-backend \
     --task-definition tailortalk-backend:1 \
     --desired-count 2
   ```

#### Using AWS Lambda (Serverless)

1. **Create Lambda function**
   ```bash
   # Package the application
   pip install -r requirements.txt -t package/
   cp -r backend package/
   cd package && zip -r ../lambda-deployment.zip .
   ```

2. **Deploy to Lambda**
   ```bash
   aws lambda create-function \
     --function-name tailortalk-backend \
     --runtime python3.9 \
     --handler backend.main.handler \
     --zip-file fileb://lambda-deployment.zip
   ```

### Google Cloud Platform

#### Using Cloud Run

1. **Build and push image**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/tailortalk
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy tailortalk-backend \
     --image gcr.io/PROJECT_ID/tailortalk \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Azure Deployment

#### Using Azure Container Instances

1. **Build and push to Azure Container Registry**
   ```bash
   az acr build --registry yourregistry --image tailortalk:latest .
   ```

2. **Deploy to Container Instances**
   ```bash
   az container create \
     --resource-group your-rg \
     --name tailortalk-backend \
     --image yourregistry.azurecr.io/tailortalk:latest \
     --ports 8000
   ```

## Environment Configuration

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Google Calendar Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback

# Application Configuration
APP_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Google Calendar Setup

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable APIs**
   - Enable Google Calendar API
   - Enable Google+ API (if needed)

3. **Create OAuth 2.0 Credentials**
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID
   - Set authorized redirect URIs
   - Download credentials as `credentials.json`

4. **Configure OAuth Consent Screen**
   - Add necessary scopes
   - Add test users (for development)

## Monitoring and Logging

### Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### Health Checks

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "openai": check_openai_connection(),
            "google_calendar": check_calendar_connection()
        }
    }
```

### Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.inc()
    request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## Security Considerations

### API Security

1. **Rate Limiting**
   ```python
   from slowapi import Limiter, _rate_limit_exceeded_handler
   from slowapi.util import get_remote_address
   from slowapi.errors import RateLimitExceeded

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

   @app.post("/chat")
   @limiter.limit("10/minute")
   async def chat_with_agent(request: Request, chat_request: ChatRequest):
       # Implementation
   ```

2. **CORS Configuration**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],
       allow_credentials=True,
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **Input Validation**
   ```python
   from pydantic import BaseModel, validator

   class ChatRequest(BaseModel):
       message: str
       
       @validator('message')
       def validate_message(cls, v):
           if len(v) > 1000:
               raise ValueError('Message too long')
           if not v.strip():
               raise ValueError('Message cannot be empty')
           return v.strip()
   ```

### Environment Security

1. **Secrets Management**
   - Use environment variables for sensitive data
   - Never commit secrets to version control
   - Use secret management services (AWS Secrets Manager, Azure Key Vault)

2. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Use VPC for cloud deployments

3. **Authentication**
   - Implement proper OAuth flow
   - Use secure session management
   - Implement API key rotation

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Check Python path
   export PYTHONPATH="${PYTHONPATH}:/path/to/project"
   
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

2. **Google Calendar Authentication**
   ```bash
   # Clear cached credentials
   rm token.json
   
   # Check credentials file
   python -c "import json; json.load(open('credentials.json'))"
   ```

3. **Port Conflicts**
   ```bash
   # Check port usage
   lsof -i :8000
   lsof -i :8501
   
   # Kill process using port
   kill -9 <PID>
   ```

### Performance Optimization

1. **Database Connection Pooling**
2. **Caching (Redis)**
3. **Load Balancing**
4. **CDN for Static Assets**

## Support

For deployment issues or questions:

1. Check the [README.md](README.md) for basic setup
2. Review the [demo.py](demo.py) for usage examples
3. Run [test_installation.py](test_installation.py) to verify setup
4. Check logs in the `logs/` directory

---

**Note**: This deployment guide covers the most common deployment scenarios. For specific cloud provider requirements or enterprise deployments, refer to the respective provider's documentation. 