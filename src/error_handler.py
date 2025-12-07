import logging
import streamlit as st
from functools import wraps

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
    )

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in {func.__name__}: {str(e)}")
            st.error(f"An error occurred: {str(e)}")
            return None
    return wrapper

def validate_file_upload(file, max_size_mb=100, allowed_types=None):
    if not file:
        return False, "No file uploaded"
    
    if file.size > max_size_mb * 1024 * 1024:
        return False, f"File too large. Max size: {max_size_mb}MB"
    
    if allowed_types and file.type not in allowed_types:
        return False, f"Invalid file type. Allowed: {allowed_types}"
    
    return True, "Valid file"