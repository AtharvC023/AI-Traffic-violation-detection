import cv2
import os
from datetime import datetime

def capture_violation_screenshot(frame, violation_type, vehicle_id):
    """Capture and save violation screenshot"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # Include milliseconds
    filename = f"{violation_type.lower().replace(' ', '_')}_{vehicle_id}_{timestamp}.jpg"
    screenshot_path = f"outputs/violations/{filename}"
    
    # Ensure directory exists
    os.makedirs("outputs/violations", exist_ok=True)
    
    # Save screenshot
    cv2.imwrite(screenshot_path, frame)
    
    return screenshot_path