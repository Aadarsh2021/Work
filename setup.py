"""
Setup script for TailorTalk AI Appointment Booking Agent.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template."""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        return True
    return False

def main():
    """Main setup function."""
    print("🚀 TailorTalk AI Appointment Booking Agent Setup")
    print("=" * 50)
    
    if not check_python_version():
        return
    
    if not install_dependencies():
        return
    
    create_env_file()
    
    print("\n🎉 Setup completed!")
    print("\n📚 Next Steps:")
    print("1. Edit .env file with your OpenAI API key")
    print("2. Set up Google Calendar credentials")
    print("3. Start the backend: python backend/main.py")
    print("4. Start the frontend: streamlit run frontend/app.py")

if __name__ == "__main__":
    main()