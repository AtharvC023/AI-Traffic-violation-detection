import cv2
import os
from datetime import datetime

def capture_violation_screenshot(frame, violation_data, vehicle_bbox, violation_type):
    """
    Capture and save violation screenshot with annotations
    
    Args:
        frame: Current video frame
        violation_data: Dictionary with violation details
        vehicle_bbox: Bounding box of violating vehicle [x1, y1, x2, y2]
        violation_type: Type of violation (e.g., 'helmet', 'redlight', etc.)
    
    Returns:
        str: Path to saved screenshot
    """
    os.makedirs('outputs/violations', exist_ok=True)
    
    # Create annotated frame
    annotated_frame = frame.copy()
    x1, y1, x2, y2 = [int(coord) for coord in vehicle_bbox]
    
    # Draw red rectangle around violating vehicle
    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 6)
    
    # Add violation label
    label = f"🚨 {violation_type.replace('_', ' ').upper()} VIOLATION"
    cv2.putText(annotated_frame, label, (x1, y1-30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)
    
    # Add timestamp
    timestamp_text = f"Time: {datetime.now().strftime('%H:%M:%S')}"
    cv2.putText(annotated_frame, timestamp_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Add confidence if available
    if 'confidence' in violation_data:
        conf_text = f"Confidence: {violation_data['confidence']:.2f}"
        cv2.putText(annotated_frame, conf_text, (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Save screenshot
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    screenshot_path = f"outputs/violations/{violation_type}_{violation_data.get('vehicle_id', 'unknown')}_{timestamp}.jpg"
    
    cv2.imwrite(screenshot_path, annotated_frame)
    return screenshot_path

def save_violation_with_screenshot(violation_type, vehicle_id, frame, vehicle_bbox, 
                                 location="Live Detection", gps_coords="0.0,0.0", 
                                 camera_id="Live Camera", confidence=None):
    """
    Save violation to database with screenshot
    
    Args:
        violation_type: Type of violation
        vehicle_id: Unique vehicle identifier
        frame: Current video frame
        vehicle_bbox: Vehicle bounding box
        location: Location of violation
        gps_coords: GPS coordinates
        camera_id: Camera identifier
        confidence: Detection confidence
    """
    import sqlite3
    
    # Capture screenshot
    violation_data = {
        'vehicle_id': vehicle_id,
        'confidence': confidence or 0.0
    }
    
    screenshot_path = capture_violation_screenshot(frame, violation_data, vehicle_bbox, violation_type)
    
    # Save to database
    conn = sqlite3.connect('current_session.db')
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS violations (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                violation_type TEXT,
                image_path TEXT,
                vehicle_id TEXT,
                location TEXT,
                gps_coords TEXT,
                camera_id TEXT
            )
        ''')

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO violations (timestamp, violation_type, image_path, vehicle_id, location, gps_coords, camera_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, violation_type, screenshot_path, vehicle_id, location, gps_coords, camera_id))
        conn.commit()
        
        print(f"✅ Violation saved with screenshot: {violation_type} - {screenshot_path}")
        
    except Exception as e:
        print(f"❌ Error saving violation: {e}")
    finally:
        conn.close()
    
    return screenshot_path