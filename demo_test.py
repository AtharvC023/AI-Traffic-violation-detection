import cv2
import numpy as np
import sys
sys.path.append('src')
from local_processor import LocalTrafficProcessor

def create_realistic_test_video():
    """Create a video that will actually trigger violations"""
    print("📹 Creating realistic test video...")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('data/samples/realistic_traffic.mp4', fourcc, 10.0, (640, 480))
    
    for frame_num in range(60):  # 6 second video
        # Create black frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw road (gray)
        cv2.rectangle(frame, (0, 300), (640, 400), (100, 100, 100), -1)
        cv2.line(frame, (320, 300), (320, 400), (255, 255, 255), 2)  # Lane divider
        
        # Draw traffic light pole
        cv2.rectangle(frame, (300, 100), (340, 300), (139, 69, 19), -1)
        
        # Traffic light - RED for first 30 frames, GREEN for rest
        if frame_num < 30:
            cv2.circle(frame, (320, 150), 15, (0, 0, 255), -1)  # RED
        else:
            cv2.circle(frame, (320, 180), 15, (0, 255, 0), -1)  # GREEN
        
        # Moving car - enters intersection during red light
        car_x = 50 + (frame_num * 10)
        if car_x < 640:
            # Car body (blue rectangle)
            cv2.rectangle(frame, (car_x, 340), (car_x + 80, 380), (255, 0, 0), -1)
            # Car windows
            cv2.rectangle(frame, (car_x + 10, 345), (car_x + 70, 365), (200, 200, 200), -1)
        
        out.write(frame)
    
    out.release()
    print("✅ Realistic test video created!")

def test_upload_process():
    """Simulate what happens when you upload a video"""
    print("\n🔄 SIMULATING VIDEO UPLOAD PROCESS...")
    print("=" * 50)
    
    # Step 1: Create test video
    create_realistic_test_video()
    
    # Step 2: Process like the dashboard would
    print("📊 Step 1: User uploads video to dashboard")
    print("📊 Step 2: System starts processing...")
    
    processor = LocalTrafficProcessor()
    
    # Step 3: Process each frame
    print("📊 Step 3: Analyzing frames...")
    cap = cv2.VideoCapture('data/samples/realistic_traffic.mp4')
    
    frame_count = 0
    total_violations = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % 10 == 0:  # Process every 10th frame
            print(f"   🔍 Processing frame {frame_count}...")
            
            # Run detection
            results = processor.model(frame)
            violations = processor.detect_violations(frame, frame_count)
            
            # Show what was detected
            cars_detected = 0
            lights_detected = 0
            
            for r in results:
                for box in r.boxes:
                    if box.cls == 2:  # car
                        cars_detected += 1
                    elif box.cls == 9:  # traffic light
                        lights_detected += 1
            
            print(f"      Cars: {cars_detected}, Lights: {lights_detected}, Violations: {len(violations)}")
            
            # Save violations
            for violation in violations:
                processor.save_violation(violation, frame)
                total_violations += 1
                print(f"      🚨 VIOLATION DETECTED: {violation['type']}")
        
        frame_count += 1
    
    cap.release()
    
    # Step 4: Show final results
    print(f"\n📊 Step 4: Processing complete!")
    print(f"🚨 Total violations found: {total_violations}")
    
    # Step 5: Show what dashboard would display
    import sqlite3
    conn = sqlite3.connect('violations.db')
    cursor = conn.execute("SELECT * FROM violations ORDER BY timestamp DESC LIMIT 5")
    
    print(f"\n📋 Dashboard would show:")
    for row in cursor.fetchall():
        print(f"   - {row[2]} at {row[1][:19]}")
        print(f"     Image: {row[3]}")
    
    conn.close()
    
    print(f"\n✅ UPLOAD SIMULATION COMPLETE!")
    print(f"💡 In real dashboard: User sees {total_violations} violations with images")

if __name__ == "__main__":
    test_upload_process()