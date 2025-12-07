#!/usr/bin/env python3
"""
One-click deployment helper
"""
import subprocess
import sys
import os

def deploy():
    print("🚀 DEPLOYING TRAFFIC VIOLATION DETECTION SYSTEM")
    print("=" * 50)
    
    # Test locally first
    print("1. Testing locally...")
    try:
        subprocess.run([sys.executable, "-c", "import streamlit; import ultralytics"], check=True)
        print("✅ Dependencies OK")
    except:
        print("❌ Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check files
    required = ["streamlit_app.py", "requirements.txt", "packages.txt"]
    for file in required:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ Missing {file}")
            return
    
    print("\n🎯 READY FOR DEPLOYMENT!")
    print("\nNext steps:")
    print("1. Push to GitHub:")
    print("   git add .")
    print("   git commit -m 'Deploy traffic detection'")
    print("   git push")
    print("\n2. Deploy on Streamlit Cloud:")
    print("   → https://share.streamlit.io")
    print("   → Connect your repo")
    print("   → Deploy!")
    
    # Start local preview
    choice = input("\nStart local preview? (y/n): ")
    if choice.lower() == 'y':
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"])

if __name__ == "__main__":
    deploy()