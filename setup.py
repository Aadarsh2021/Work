"""
Setup script for TailorTalk AI Appointment Booking Agent.
"""

from setuptools import setup, find_packages

setup(
    name="tailortalk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "streamlit==1.28.1",
        "python-dotenv==1.0.0",
        "pydantic==2.5.0",
        "langchain==0.1.0",
        "langchain-openai==0.0.5",
        "langgraph==0.0.20",
        "openai<2.0.0,>=1.10.0",
        "google-auth==2.23.4",
        "google-auth-oauthlib==1.1.0",
        "google-auth-httplib2==0.1.1",
        "google-api-python-client==2.108.0",
        "pytz==2023.3",
        "slowapi==0.1.9",
        "redis==5.0.1",
        "prometheus-client==0.19.0",
        "python-multipart==0.0.6"
    ],
    python_requires=">=3.10",
)