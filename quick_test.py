#!/usr/bin/env python3
"""
Quick test script - just run this to see if everything works
"""

import os
import sys
sys.path.append('src')

from local_processor import LocalTrafficProcessor

def test_system():
    print("🚦 Testing Traffic Violation System...")
    print("=" * 40)
    
    # Check if sample video exists
    if not os.path.exists("data/samples/traffic_sample.mp4"):
        print("❌ No sample video found")
        print("📥 Creating a test video...")
        
        import cv2
        import numpy as np
        
        # Create simple test video with moving rectangles (cars)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('data/samples/traffic_sample.mp4', fourcc, 10.0, (640, 480))
        
        for i in range(50):
            # Create frame with moving "car"
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Draw road
            cv2.rectangle(frame, (0, 200), (640, 280), (50, 50, 50), -1)
            # Draw moving car
            car_x = (i * 10) % 600
            cv2.rectangle(frame, (car_x, 220), (car_x + 60, 260), (0, 0, 255), -1)
            # Draw traffic light
            cv2.circle(frame, (320, 150), 20, (0, 255, 0), -1)  # Green light
            if i > 25:  # Red light after frame 25
                cv2.circle(frame, (320, 150), 20, (0, 0, 255), -1)
            
            out.write(frame)
        
        out.release()
        print("✅ Test video created!")
    
    # Test the processor
    print("🔍 Processing video...")
    processor = LocalTrafficProcessor()
    processor.process_video("data/samples/traffic_sample.mp4")
    
    print("✅ Processing complete!")
    print("📊 Check violations.db for results")
    
    # Show results
    import sqlite3
    conn = sqlite3.connect('violations.db')
    cursor = conn.execute("SELECT COUNT(*) FROM violations")
    count = cursor.fetchone()[0]
    print(f"🚨 Found {count} violations")
    
    if count > 0:
        cursor = conn.execute("SELECT * FROM violations LIMIT 3")
        print("\n📋 Sample violations:")
        for row in cursor.fetchall():
            print(f"  - {row[2]} at {row[1]}")
    
    conn.close()
    print("\n🎉 System is working!")
    print("💡 Now run: streamlit run src/free_dashboard.py")

if __name__ == "__main__":
    test_system()