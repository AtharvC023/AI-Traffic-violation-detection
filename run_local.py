#!/usr/bin/env python3
"""
Quick start script for local traffic violation detection
"""

import os
import subprocess
import sys

def install_requirements():
    print("Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def download_sample_video():
    print("You need to add a sample video to data/samples/")
    print("Download any traffic video from YouTube or use your phone to record traffic")
    print("Save it as: data/samples/traffic_sample.mp4")

def run_dashboard():
    print("Starting dashboard...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "src/free_dashboard.py", "--server.port=8501", "--server.address=127.0.0.1"])

if __name__ == "__main__":
    print("Traffic Violation Detection - Free Version")
    print("=" * 50)
    
    choice = input("Choose option:\n1. Install requirements\n2. Run dashboard\n3. Process sample video\nEnter (1-3): ")
    
    if choice == "1":
        install_requirements()
    elif choice == "2":
        run_dashboard()
    elif choice == "3":
        if os.path.exists("data/samples/traffic_sample.mp4"):
            from src.local_processor import LocalTrafficProcessor
            processor = LocalTrafficProcessor()
            processor.process_video("data/samples/traffic_sample.mp4")
        else:
            download_sample_video()
    else:
        print("Invalid choice")