import cv2
import streamlit as st
import os
from datetime import datetime
from ultralytics import YOLO
from license_plate_recognition import LicensePlateRecognizer
from screenshot_handler import capture_violation_screenshot

def run_live_camera():
    """Run live camera with real-time detection"""
    model = YOLO('yolov8n.pt')
    plate_recognizer = LicensePlateRecognizer()
    
    # Try different camera indices
    cap = None
    for camera_id in [0, 1, -1]:
        cap = cv2.VideoCapture(camera_id)
        if cap.isOpened():
            break
        cap.release()
    
    if cap is None or not cap.isOpened():
        st.error("❌ Cannot access camera. Please check camera permissions and ensure no other app is using the camera.")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    st.success("✅ Camera connected successfully!")
    
    frame_count = 0
    violations_found = 0
    live_violations = []
    violated_vehicles = set()
    detected_plates = []
    
    vehicle_classes = {
        2: ('cars', 'Car', (0, 255, 0)),
        3: ('motorcycles', 'Motorcycle', (255, 0, 255)),
        5: ('buses', 'Bus', (0, 255, 255)),
        7: ('trucks', 'Truck', (255, 255, 0))
    }
    
    # COCO class names for identification
    class_names = {
        0: 'Person', 1: 'Bicycle', 2: 'Car', 3: 'Motorcycle', 4: 'Airplane',
        5: 'Bus', 6: 'Train', 7: 'Truck', 8: 'Boat', 9: 'Traffic Light',
        10: 'Fire Hydrant', 11: 'Stop Sign', 12: 'Parking Meter', 13: 'Bench'
    }
    
    camera_placeholder = st.empty()
    stats_placeholder = st.empty()
    violations_placeholder = st.empty()
    
    while st.session_state.get('camera_active', False):
        ret, frame = cap.read()
        if not ret:
            break
        
        results = model(frame, conf=0.3)
        annotated_frame = frame.copy()
        
        # License plates
        plates_data = plate_recognizer.recognize_license_plate(frame)
        if plates_data:
            annotated_frame = plate_recognizer.draw_plates(annotated_frame, plates_data)
            for plate in plates_data:
                detected_plates.append({
                    'frame': frame_count,
                    'plate_number': plate['plate_number'],
                    'time': datetime.now().strftime('%H:%M:%S')
                })
        
        current_violations = 0
        vehicles = {'cars': [], 'motorcycles': [], 'buses': [], 'trucks': []}
        persons = []
        
        # COCO class names for identification
        class_names = {
            0: 'Person', 1: 'Bicycle', 2: 'Car', 3: 'Motorcycle', 4: 'Airplane',
            5: 'Bus', 6: 'Train', 7: 'Truck', 8: 'Boat', 9: 'Traffic Light',
            10: 'Fire Hydrant', 11: 'Stop Sign', 12: 'Parking Meter', 13: 'Bench'
        }
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                conf = float(box.conf)
                cls = int(box.cls)
                
                # Get class name
                class_name = class_names.get(cls, f'Object_{cls}')
                
                if cls in vehicle_classes:
                    vehicle_type, label, color = vehicle_classes[cls]
                    vehicles[vehicle_type].append((x1, y1, x2, y2, conf))
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated_frame, f"{label} {conf:.2f}", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                elif cls == 0:  # Person
                    persons.append((x1, y1, x2, y2, conf))
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.putText(annotated_frame, f"Person {conf:.2f}", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                elif cls == 9:  # Traffic Light
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                    cv2.putText(annotated_frame, f"Traffic Light {conf:.2f}", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                elif cls == 11:  # Stop Sign
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(annotated_frame, f"Stop Sign {conf:.2f}", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                elif cls == 1:  # Bicycle
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.putText(annotated_frame, f"Bicycle {conf:.2f}", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                else:
                    # Show other detected objects
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (128, 128, 128), 1)
                    cv2.putText(annotated_frame, f"{class_name} {conf:.2f}", (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (128, 128, 128), 1)
        
        # Check for various violations
        
        # 1. Helmet violations for motorcycles
        for mx1, my1, mx2, my2, mconf in vehicles['motorcycles']:
            vehicle_id = f"bike_{int(mx1/50)}_{int(my1/50)}"
            if vehicle_id in violated_vehicles:
                continue
                
            helmet_violation = False
            for px1, py1, px2, py2, pconf in persons:
                if (px1 < mx2 and px2 > mx1 and py1 < my2 and py2 > my1):
                    head_height = int((py2 - py1) * 0.2)
                    head_region = frame[py1:py1 + head_height, px1:px2]
                    if head_region.size > 0:
                        gray = cv2.cvtColor(head_region, cv2.COLOR_BGR2GRAY)
                        mask = (gray < 80).astype('uint8')
                        dark_pixels = cv2.countNonZero(mask)
                        total_pixels = gray.shape[0] * gray.shape[1]
                        if dark_pixels < total_pixels * 0.3:
                            helmet_violation = True
                            break
            
            if helmet_violation:
                violated_vehicles.add(vehicle_id)
                current_violations += 1
                violations_found += 1
                cv2.rectangle(annotated_frame, (mx1, my1), (mx2, my2), (0, 0, 255), 4)
                cv2.putText(annotated_frame, "NO HELMET", (mx1, my1-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                screenshot_path = capture_violation_screenshot(annotated_frame, 'No Helmet Violation', vehicle_id)
                from free_dashboard import save_violation_to_db
                save_violation_to_db('No Helmet Violation', vehicle_id, screenshot_path, "Live Camera")
                
                live_violations.append({
                    'type': 'No Helmet Violation',
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'screenshot': screenshot_path
                })
        
        # 2. Speeding violations (simplified detection)
        for vehicle_type, vehicle_list in vehicles.items():
            for vx1, vy1, vx2, vy2, vconf in vehicle_list:
                vehicle_id = f"{vehicle_type[:-1]}_{int(vx1/50)}_{int(vy1/50)}"
                if vehicle_id in violated_vehicles:
                    continue
                
                # Simple speed check based on frame movement
                if frame_count > 10 and vconf > 0.7:  # High confidence fast-moving vehicle
                    if abs(vx2 - vx1) > 150 or abs(vy2 - vy1) > 100:  # Large bounding box = close/fast
                        violated_vehicles.add(vehicle_id)
                        current_violations += 1
                        violations_found += 1
                        cv2.rectangle(annotated_frame, (vx1, vy1), (vx2, vy2), (0, 0, 255), 4)
                        cv2.putText(annotated_frame, "SPEEDING", (vx1, vy1-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        screenshot_path = capture_violation_screenshot(annotated_frame, 'Speeding Violation', vehicle_id)
                        from free_dashboard import save_violation_to_db
                        save_violation_to_db('Speeding Violation', vehicle_id, screenshot_path, "Live Camera")
                        
                        live_violations.append({
                            'type': 'Speeding Violation',
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'screenshot': screenshot_path
                        })
        
        # 3. Wrong way violations (vehicles moving upward)
        for vehicle_type, vehicle_list in vehicles.items():
            for vx1, vy1, vx2, vy2, vconf in vehicle_list:
                vehicle_id = f"{vehicle_type[:-1]}_{int(vx1/50)}_{int(vy1/50)}"
                if vehicle_id in violated_vehicles:
                    continue
                
                # Check if vehicle is in upper part of frame (wrong direction)
                if vy1 < frame.shape[0] * 0.3 and vconf > 0.6:
                    violated_vehicles.add(vehicle_id)
                    current_violations += 1
                    violations_found += 1
                    cv2.rectangle(annotated_frame, (vx1, vy1), (vx2, vy2), (0, 0, 255), 4)
                    cv2.putText(annotated_frame, "WRONG WAY", (vx1, vy1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    screenshot_path = capture_violation_screenshot(annotated_frame, 'Wrong Way Violation', vehicle_id)
                    from free_dashboard import save_violation_to_db
                    save_violation_to_db('Wrong Way Violation', vehicle_id, screenshot_path, "Live Camera")
                    
                    live_violations.append({
                        'type': 'Wrong Way Violation',
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'screenshot': screenshot_path
                    })
        

        
        if current_violations > 0:
            cv2.rectangle(annotated_frame, (10, 10), (300, 50), (0, 0, 255), -1)
            cv2.putText(annotated_frame, f"VIOLATIONS: {current_violations}", 
                      (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Display live feed
        camera_placeholder.image(annotated_frame, channels="BGR", use_container_width=True)
        
        # Count all detected objects
        object_counts = {}
        for r in results:
            for box in r.boxes:
                cls = int(box.cls)
                class_name = class_names.get(cls, f'Object_{cls}')
                object_counts[class_name] = object_counts.get(class_name, 0) + 1
        
        # Update stats
        with stats_placeholder.container():
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Frame", frame_count)
            with col2:
                total_vehicles = sum(len(v) for v in vehicles.values())
                st.metric("Vehicles", total_vehicles)
            with col3:
                st.metric("Violations", violations_found)
            
            # Show detected objects
            if object_counts:
                st.write("**Detected Objects:**")
                for obj_name, count in object_counts.items():
                    if count > 0:
                        emoji = {
                            'Person': '👤', 'Car': '🚗', 'Motorcycle': '🏍️', 
                            'Bus': '🚌', 'Truck': '🚛', 'Bicycle': '🚲',
                            'Traffic Light': '🚦', 'Stop Sign': '🛑'
                        }.get(obj_name, '📦')
                        st.write(f"{emoji} {obj_name}: {count}")
            
            if detected_plates:
                st.write("**Recent Plates:**")
                for plate in detected_plates[-3:]:
                    st.write(f"🚗 {plate['plate_number']} ({plate['time']})")
        
        # Categorize live violations
        from violation_categories import VIOLATION_CATEGORIES, get_violation_category, get_violation_emoji
        
        violation_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        for violation in live_violations:
            category = get_violation_category(violation['type'])
            violation_counts[category] += 1
        
        with violations_placeholder.container():
            st.write("**📊 Live Violation Categories**")
            
            # Show category counters
            for category, data in VIOLATION_CATEGORIES.items():
                count = violation_counts[category]
                if count > 0:
                    st.write(f"{data['color']} **{category}**: {count}")
            
            st.write("---")
            st.write("**🚨 Latest Violations**")
            
            if live_violations:
                for violation in live_violations[-3:]:
                    emoji = get_violation_emoji(violation['type'])
                    category = get_violation_category(violation['type'])
                    color = VIOLATION_CATEGORIES[category]['color']
                    st.write(f"{color} {emoji} {violation['type']} - {violation['time']}")
                    if 'screenshot' in violation:
                        st.write(f"   📷 Screenshot saved")
            else:
                st.write("🟢 **No violations detected**")
            
            # Show latest violation screenshot
            if live_violations:
                latest_violation = live_violations[-1]
                if 'screenshot' in latest_violation and os.path.exists(latest_violation['screenshot']):
                    emoji = get_violation_emoji(latest_violation['type'])
                    st.write(f"**{emoji} Latest Evidence:**")
                    st.image(latest_violation['screenshot'], 
                           caption=f"{latest_violation['type']} - {latest_violation['time']}", 
                           width=200)
        
        frame_count += 1
    
    cap.release()