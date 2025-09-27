#!/usr/bin/env python3
"""
Deployment helper script for Traffic Violation Detection
"""

import os
import subprocess
import sys

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'streamlit_app.py',
        'requirements.txt',
        'packages.txt',
        'src/free_dashboard.py',
        'yolov8n.pt'
    ]

    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)

    if missing:
        print("Missing required files:")
        for file in missing:
            print(f"   - {file}")
        return False

    print("All required files present")
    return True

def test_local():
    """Test the application locally"""
    print("Testing locally...")
    try:
        # Test import
        subprocess.run([sys.executable, '-c', 'import streamlit_app'], check=True)
        print("Import test passed")
        return True
    except subprocess.CalledProcessError:
        print("Import test failed")
        return False

def deploy_streamlit_cloud():
    """Instructions for Streamlit Cloud deployment"""
    print("\n" + "="*50)
    print("STREAMLIT CLOUD DEPLOYMENT")
    print("="*50)
    print("1. Go to: https://share.streamlit.io")
    print("2. Connect your GitHub repository")
    print("3. Streamlit will auto-detect streamlit_app.py")
    print("4. Deploy!")
    print("\nYour app will be live at a share.streamlit.io URL")

def deploy_railway():
    """Instructions for Railway deployment"""
    print("\n" + "="*50)
    print("RAILWAY DEPLOYMENT")
    print("="*50)
    print("1. Go to: https://railway.app")
    print("2. Connect your GitHub repository")
    print("3. Railway will auto-detect Python/Streamlit")
    print("4. Deploy!")
    print("\nPricing: ~$5-15/month")

def deploy_render():
    """Instructions for Render deployment"""
    print("\n" + "="*50)
    print("RENDER DEPLOYMENT")
    print("="*50)
    print("1. Go to: https://render.com")
    print("2. Connect GitHub repository")
    print("3. Choose 'Web Service'")
    print("4. Build command: pip install -r requirements.txt")
    print("5. Start command: streamlit run streamlit_app.py --server.port $PORT --server.headless true")
    print("\nPricing: Free tier + $7/month")

def deploy_docker():
    """Docker deployment instructions"""
    print("\n" + "="*50)
    print("DOCKER DEPLOYMENT")
    print("="*50)
    print("1. Build image:")
    print("   docker build -t traffic-monitor ./docker")
    print("\n2. Test locally:")
    print("   docker run -p 8501:8501 traffic-monitor")
    print("\n3. Deploy to any container service:")
    print("   - Google Cloud Run")
    print("   - AWS Fargate")
    print("   - DigitalOcean App Platform")
    print("   - Heroku Container Registry")

def main():
    print("Traffic Violation Detection - Deployment Helper")
    print("="*55)

    if not check_requirements():
        print("\nPlease ensure all required files are present before deploying.")
        return

    if not test_local():
        print("\nLocal test failed. Please fix issues before deploying.")
        return

    print("\nReady for deployment!")
    print("\nChoose your deployment platform:")

    options = {
        '1': ('Streamlit Cloud', deploy_streamlit_cloud),
        '2': ('Railway', deploy_railway),
        '3': ('Render', deploy_render),
        '4': ('Docker', deploy_docker),
        '5': ('AWS (existing)', lambda: print("\nUse your existing Terraform setup in deployment_guide.md"))
    }

    while True:
        print("\nDeployment Options:")
        for key, (name, _) in options.items():
            print(f"{key}. {name}")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice in options:
            options[choice][1]()
            break
        else:
            print("Invalid choice. Please try again.")

    print("\nFor detailed instructions, see DEPLOYMENT_README.md")
    print("Your app will be accessible via a public URL once deployed!")

if __name__ == "__main__":
    main()