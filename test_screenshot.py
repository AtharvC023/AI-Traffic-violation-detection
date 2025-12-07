#!/usr/bin/env python3
"""
Test screenshot functionality
"""
import cv2
import numpy as np
import os
from datetime import datetime

def test_screenshot_capture():
    print("📸 Testing screenshot capture...")
    
    # Create test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw road
    cv2.rectangle(frame, (0, 300), (640, 400), (100, 100, 100), -1)
    
    # Draw test vehicle
    cv2.rectangle(frame, (200, 320), (280, 380), (255, 0, 0), -1)
    
    # Create violation screenshot
    os.makedirs('outputs/violations', exist_ok=True)
    screenshot_path = f"outputs/violations/test_violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    
    # Annotate violation
    violation_frame = frame.copy()
    cv2.rectangle(violation_frame, (200, 320), (280, 380), (0, 0, 255), 6)
    cv2.putText(violation_frame, "🚨 TEST VIOLATION", (200, 310), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
    cv2.putText(violation_frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Save screenshot
    success = cv2.imwrite(screenshot_path, violation_frame)
    
    if success and os.path.exists(screenshot_path):
        print(f"✅ Screenshot saved: {screenshot_path}")
        print(f"📁 File size: {os.path.getsize(screenshot_path)} bytes")
        return screenshot_path
    else:
        print("❌ Failed to save screenshot")
        return None

if __name__ == "__main__":
    test_screenshot_capture()