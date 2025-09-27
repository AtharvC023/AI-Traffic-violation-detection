#!/usr/bin/env python3
"""
Main Streamlit application for deployment
"""

import streamlit as st
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the dashboard
from free_dashboard import main

if __name__ == "__main__":
    main()