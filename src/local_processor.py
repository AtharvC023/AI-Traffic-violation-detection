import cv2
import sqlite3
from ultralytics import YOLO
from datetime import datetime
import os
try:
    from license_plate_detector import LicensePlateDetector
except ImportError:
    LicensePlateDetector = None

class LocalTrafficProcessor:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')  # Downloads automatically
        self.setup_database()
        self.violated_vehicles = set()  # Track vehicles that already have violations
        self.vehicle_positions = {}  # Track vehicle positions for speed/movement analysis
        self.frame_rate = 30  # Assume 30 FPS for speed calculation
        self.plate_detector = LicensePlateDetector() if LicensePlateDetector else None
        
    def setup_database(self):
        self.conn = sqlite3.connect('current_session.db')
        self.conn.execute('''
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
        
    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % 30 == 0:  # Process every 30th frame
                violations = self.detect_violations(frame, frame_count)
                for violation in violations:
                    self.save_violation(violation, frame)
                    
            frame_count += 1
        cap.release()
        
    def detect_violations(self, frame, frame_num):
        results = self.model(frame, conf=0.25)
        violations = []
        
        vehicles = {'cars': [], 'motorcycles': [], 'buses': [], 'trucks': []}
        traffic_lights = []
        persons = []
        
        # COCO class mapping
        vehicle_classes = {
            2: 'cars',      # car
            3: 'motorcycles', # motorcycle  
            5: 'buses',     # bus
            7: 'trucks'     # truck
        }
        
        for r in results:
            for box in r.boxes:
                cls = int(box.cls)
                bbox = box.xyxy[0].tolist()
                conf = float(box.conf)
                
                if cls in vehicle_classes and self.is_valid_vehicle(bbox, conf, cls):
                    vehicles[vehicle_classes[cls]].append({
                        'bbox': bbox,
                        'confidence': conf,
                        'type': vehicle_classes[cls][:-1]  # Remove 's'
                    })
                elif cls == 9:  # traffic light
                    traffic_lights.append({'bbox': bbox, 'confidence': conf})
                elif cls == 0:  # person
                    persons.append({'bbox': bbox, 'confidence': conf})
        
        # Check helmet violations for motorcycles
        for motorcycle in vehicles['motorcycles']:
            # Create unique vehicle ID based on position
            mx1, my1, mx2, my2 = motorcycle['bbox']
            vehicle_id = f"bike_{int(mx1/50)}_{int(my1/50)}"
            
            # Skip if this vehicle already has a violation
            if vehicle_id in self.violated_vehicles:
                continue
                
            helmet_violation = self.check_helmet_violation(frame, motorcycle, persons)
            if helmet_violation:
                self.violated_vehicles.add(vehicle_id)  # Mark as violated
                violations.append({
                    'type': 'no_helmet_violation',
                    'frame': frame_num,
                    'confidence': motorcycle['confidence'],
                    'vehicle_position': motorcycle['bbox'],
                    'vehicle_type': 'motorcycle',
                    'location': 'Traffic Junction',
                    'gps_coords': '40.7128, -74.0060',
                    'camera_id': 'CAM_001'
                })
        
        # Check red light violations for all vehicles
        red_light_detected = self.detect_red_light(frame, traffic_lights)
        if red_light_detected:
            frame_height = frame.shape[0]
            
            for vehicle_type, vehicle_list in vehicles.items():
                for vehicle in vehicle_list:
                    vehicle_y = vehicle['bbox'][3]  # bottom of vehicle
                    
                    # Create unique vehicle ID
                    vx1, vy1, vx2, vy2 = vehicle['bbox']
                    vehicle_id = f"{vehicle['type']}_{int(vx1/50)}_{int(vy1/50)}"
                    
                    # Skip if this vehicle already has a violation
                    if vehicle_id in self.violated_vehicles:
                        continue
                        
                    # If vehicle is in intersection (bottom 30% of frame)
                    if vehicle_y > frame_height * 0.7:
                        self.violated_vehicles.add(vehicle_id)  # Mark as violated
                        violations.append({
                            'type': 'red_light_violation',
                            'frame': frame_num,
                            'confidence': vehicle['confidence'],
                            'vehicle_position': vehicle['bbox'],
                            'vehicle_type': vehicle['type'],
                            'location': 'Main St & 5th Ave Intersection',
                            'gps_coords': '40.7128, -74.0060',
                            'camera_id': 'CAM_001'
                        })
        
        # Check additional violations
        violations.extend(self.check_speeding_violations(vehicles, frame_num))
        violations.extend(self.check_wrong_way_violations(vehicles, frame_num))
        violations.extend(self.check_lane_violations(frame, vehicles, frame_num))
        violations.extend(self.check_parking_violations(vehicles, frame_num))
        violations.extend(self.check_tailgating_violations(vehicles, frame_num))
        violations.extend(self.check_crosswalk_violations(frame, vehicles, persons, frame_num))
        
        return violations
    
    def detect_traffic_light_color(self, light_region):
        """Improved traffic light color detection"""
        if light_region.size == 0:
            return 'unknown'
        
        hsv = cv2.cvtColor(light_region, cv2.COLOR_BGR2HSV)
        total_pixels = light_region.shape[0] * light_region.shape[1]
        
        # Improved color ranges
        lower_red1, upper_red1 = (0, 120, 70), (10, 255, 255)
        lower_red2, upper_red2 = (170, 120, 70), (180, 255, 255)
        red_mask = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
        red_pixels = cv2.countNonZero(red_mask)
        
        lower_yellow, upper_yellow = (15, 120, 70), (35, 255, 255)
        yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        yellow_pixels = cv2.countNonZero(yellow_mask)
        
        lower_green, upper_green = (40, 120, 70), (80, 255, 255)
        green_mask = cv2.inRange(hsv, lower_green, upper_green)
        green_pixels = cv2.countNonZero(green_mask)
        
        threshold = total_pixels * 0.08
        
        if red_pixels > threshold and red_pixels > yellow_pixels and red_pixels > green_pixels:
            return 'red'
        elif yellow_pixels > threshold and yellow_pixels > green_pixels:
            return 'yellow'
        elif green_pixels > threshold:
            return 'green'
        
        return 'unknown'
    
    def detect_red_light(self, frame, traffic_lights):
        """Check if any traffic light is red"""
        for light in traffic_lights:
            x1, y1, x2, y2 = [int(coord) for coord in light['bbox']]
            light_region = frame[y1:y2, x1:x2]
            
            if self.detect_traffic_light_color(light_region) == 'red':
                return True
        
        return False
    
    def check_speeding_violations(self, vehicles, frame_num):
        """Detect speeding by tracking vehicle movement"""
        violations = []
        speed_limit_kmh = 50  # Assume 50 km/h speed limit
        
        for vehicle_type, vehicle_list in vehicles.items():
            for vehicle in vehicle_list:
                vx1, vy1, vx2, vy2 = vehicle['bbox']
                vehicle_center = ((vx1 + vx2) / 2, (vy1 + vy2) / 2)
                vehicle_id = f"{vehicle['type']}_{int(vx1/50)}_{int(vy1/50)}"
                
                if vehicle_id in self.vehicle_positions:
                    prev_pos, prev_frame = self.vehicle_positions[vehicle_id]
                    
                    # Calculate distance moved (pixels)
                    distance_pixels = ((vehicle_center[0] - prev_pos[0])**2 + (vehicle_center[1] - prev_pos[1])**2)**0.5
                    frame_diff = frame_num - prev_frame
                    
                    if frame_diff > 0 and distance_pixels > 30:  # Significant movement
                        # Rough speed estimation (pixels per frame to km/h)
                        estimated_speed = (distance_pixels / frame_diff) * 2  # Rough conversion
                        
                        if estimated_speed > speed_limit_kmh and vehicle_id not in self.violated_vehicles:
                            self.violated_vehicles.add(vehicle_id)
                            violations.append({
                                'type': 'speeding_violation',
                                'frame': frame_num,
                                'confidence': vehicle['confidence'],
                                'vehicle_position': vehicle['bbox'],
                                'vehicle_type': vehicle['type'],
                                'estimated_speed': f"{estimated_speed:.1f} km/h",
                                'location': 'Highway Section A',
                                'gps_coords': '40.7128, -74.0060',
                                'camera_id': 'CAM_002'
                            })
                
                self.vehicle_positions[vehicle_id] = (vehicle_center, frame_num)
        
        return violations
    
    def check_wrong_way_violations(self, vehicles, frame_num):
        """Detect vehicles moving against traffic flow"""
        violations = []
        
        for vehicle_type, vehicle_list in vehicles.items():
            for vehicle in vehicle_list:
                vx1, vy1, vx2, vy2 = vehicle['bbox']
                vehicle_id = f"{vehicle['type']}_{int(vx1/50)}_{int(vy1/50)}"
                
                if vehicle_id in self.vehicle_positions:
                    prev_pos, prev_frame = self.vehicle_positions[vehicle_id]
                    current_pos = ((vx1 + vx2) / 2, (vy1 + vy2) / 2)
                    
                    # Check if moving upward (wrong way on typical road)
                    if current_pos[1] < prev_pos[1] - 20 and vehicle_id not in self.violated_vehicles:
                        self.violated_vehicles.add(vehicle_id)
                        violations.append({
                            'type': 'wrong_way_violation',
                            'frame': frame_num,
                            'confidence': vehicle['confidence'],
                            'vehicle_position': vehicle['bbox'],
                            'vehicle_type': vehicle['type'],
                            'location': 'One-way Street',
                            'gps_coords': '40.7128, -74.0060',
                            'camera_id': 'CAM_003'
                        })
        
        return violations
    
    def check_lane_violations(self, frame, vehicles, frame_num):
        """Detect lane violations using edge detection"""
        violations = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        frame_width = frame.shape[1]
        center_line = frame_width // 2
        
        for vehicle_type, vehicle_list in vehicles.items():
            for vehicle in vehicle_list:
                vx1, vy1, vx2, vy2 = vehicle['bbox']
                vehicle_center_x = (vx1 + vx2) / 2
                vehicle_id = f"{vehicle['type']}_{int(vx1/50)}_{int(vy1/50)}"
                
                # Check if vehicle is crossing center line
                if abs(vehicle_center_x - center_line) < 50 and vehicle_id not in self.violated_vehicles:
                    self.violated_vehicles.add(vehicle_id)
                    violations.append({
                        'type': 'lane_violation',
                        'frame': frame_num,
                        'confidence': vehicle['confidence'],
                        'vehicle_position': vehicle['bbox'],
                        'vehicle_type': vehicle['type'],
                        'location': 'Main Road',
                        'gps_coords': '40.7128, -74.0060',
                        'camera_id': 'CAM_004'
                    })
        
        return violations
    
    def check_parking_violations(self, vehicles, frame_num):
        """Detect vehicles parked in no-parking zones"""
        violations = []
        
        for vehicle_type, vehicle_list in vehicles.items():
            for vehicle in vehicle_list:
                vx1, vy1, vx2, vy2 = vehicle['bbox']
                vehicle_id = f"{vehicle['type']}_{int(vx1/50)}_{int(vy1/50)}"
                
                # Check if vehicle hasn't moved (stationary)
                if vehicle_id in self.vehicle_positions:
                    prev_pos, prev_frame = self.vehicle_positions[vehicle_id]
                    current_pos = ((vx1 + vx2) / 2, (vy1 + vy2) / 2)
                    
                    distance_moved = ((current_pos[0] - prev_pos[0])**2 + (current_pos[1] - prev_pos[1])**2)**0.5
                    frames_stationary = frame_num - prev_frame
                    
                    # If stationary for 5+ seconds (150 frames) in roadway
                    if distance_moved < 10 and frames_stationary > 150 and vy2 > 300:
                        if vehicle_id not in self.violated_vehicles:
                            self.violated_vehicles.add(vehicle_id)
                            violations.append({
                                'type': 'illegal_parking_violation',
                                'frame': frame_num,
                                'confidence': vehicle['confidence'],
                                'vehicle_position': vehicle['bbox'],
                                'vehicle_type': vehicle['type'],
                                'location': 'No Parking Zone',
                                'gps_coords': '40.7128, -74.0060',
                                'camera_id': 'CAM_005'
                            })
        
        return violations
    
    def check_tailgating_violations(self, vehicles, frame_num):
        """Detect vehicles following too closely"""
        violations = []
        
        for vehicle_type, vehicle_list in vehicles.items():
            for i, vehicle1 in enumerate(vehicle_list):
                for j, vehicle2 in enumerate(vehicle_list[i+1:], i+1):
                    v1x1, v1y1, v1x2, v1y2 = vehicle1['bbox']
                    v2x1, v2y1, v2x2, v2y2 = vehicle2['bbox']
                    
                    # Calculate distance between vehicles
                    center1 = ((v1x1 + v1x2) / 2, (v1y1 + v1y2) / 2)
                    center2 = ((v2x1 + v2x2) / 2, (v2y1 + v2y2) / 2)
                    distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
                    
                    # If vehicles are too close (less than 80 pixels apart)
                    if distance < 80 and abs(center1[0] - center2[0]) < 50:  # Same lane
                        vehicle_id = f"{vehicle1['type']}_{int(v1x1/50)}_{int(v1y1/50)}"
                        if vehicle_id not in self.violated_vehicles:
                            self.violated_vehicles.add(vehicle_id)
                            violations.append({
                                'type': 'tailgating_violation',
                                'frame': frame_num,
                                'confidence': vehicle1['confidence'],
                                'vehicle_position': vehicle1['bbox'],
                                'vehicle_type': vehicle1['type'],
                                'location': 'Highway',
                                'gps_coords': '40.7128, -74.0060',
                                'camera_id': 'CAM_006'
                            })
        
        return violations
    
    def check_crosswalk_violations(self, frame, vehicles, persons, frame_num):
        """Detect vehicles not yielding to pedestrians in crosswalk"""
        violations = []
        frame_height, frame_width = frame.shape[:2]
        
        # Define crosswalk area (middle section of frame)
        crosswalk_y1 = int(frame_height * 0.4)
        crosswalk_y2 = int(frame_height * 0.6)
        
        # Check if pedestrians are in crosswalk
        pedestrians_in_crosswalk = []
        for person in persons:
            px1, py1, px2, py2 = person['bbox']
            if crosswalk_y1 < py2 < crosswalk_y2:
                pedestrians_in_crosswalk.append(person)
        
        # If pedestrians present, check for vehicle violations
        if pedestrians_in_crosswalk:
            for vehicle_type, vehicle_list in vehicles.items():
                for vehicle in vehicle_list:
                    vx1, vy1, vx2, vy2 = vehicle['bbox']
                    vehicle_id = f"{vehicle['type']}_{int(vx1/50)}_{int(vy1/50)}"
                    
                    # Check if vehicle is in crosswalk area
                    if crosswalk_y1 < vy2 < crosswalk_y2 and vehicle_id not in self.violated_vehicles:
                        self.violated_vehicles.add(vehicle_id)
                        violations.append({
                            'type': 'crosswalk_violation',
                            'frame': frame_num,
                            'confidence': vehicle['confidence'],
                            'vehicle_position': vehicle['bbox'],
                            'vehicle_type': vehicle['type'],
                            'location': 'Pedestrian Crosswalk',
                            'gps_coords': '40.7128, -74.0060',
                            'camera_id': 'CAM_007'
                        })
        
        return violations
    
    def is_valid_vehicle(self, bbox, confidence, vehicle_class):
        """Validate if detection is actually a vehicle"""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        area = width * height
        aspect_ratio = width / height if height > 0 else 0
        
        # Minimum confidence thresholds
        min_confidence = {
            2: 0.4,   # car - higher threshold
            3: 0.35,  # motorcycle
            5: 0.5,   # bus - higher threshold
            7: 0.45   # truck
        }
        
        if confidence < min_confidence.get(vehicle_class, 0.3):
            return False
        
        # Size filters - reject too small/large detections
        if area < 1000 or area > 200000:  # Reasonable vehicle size range
            return False
        
        # Aspect ratio filters
        if vehicle_class == 2:  # car
            if aspect_ratio < 0.8 or aspect_ratio > 3.0:  # Cars are wider than tall
                return False
        elif vehicle_class == 3:  # motorcycle
            if aspect_ratio < 0.3 or aspect_ratio > 2.5:
                return False
        elif vehicle_class in [5, 7]:  # bus/truck
            if aspect_ratio < 0.5 or aspect_ratio > 4.0:
                return False
        
        # Reject detections that are too thin (likely lines/markings)
        if width < 30 or height < 30:
            return False
        
        # Reject extremely elongated shapes (zebra crossings, lane markings)
        if aspect_ratio > 5.0 or aspect_ratio < 0.2:
            return False
            
        return True
        
    def check_helmet_violation(self, frame, motorcycle, persons):
        """Check if motorcycle rider is wearing helmet"""
        mx1, my1, mx2, my2 = motorcycle['bbox']
        
        # Find persons near motorcycle
        for person in persons:
            px1, py1, px2, py2 = person['bbox']
            
            # Check if person overlaps with motorcycle area
            if (px1 < mx2 and px2 > mx1 and py1 < my2 and py2 > my1):
                # Extract head region (top 20% of person)
                head_height = int((py2 - py1) * 0.2)
                head_region = frame[int(py1):int(py1 + head_height), int(px1):int(px2)]
                
                if head_region.size > 0:
                    # Simple helmet detection using color analysis
                    # Helmets are usually dark colored (black, blue, etc.)
                    gray = cv2.cvtColor(head_region, cv2.COLOR_BGR2GRAY)
                    mask = (gray < 80).astype('uint8')
                    dark_pixels = cv2.countNonZero(mask)
                    total_pixels = gray.shape[0] * gray.shape[1]
                    
                    # If less than 30% dark pixels, likely no helmet
                    if dark_pixels < total_pixels * 0.3:
                        return True
        return False
    
    def save_violation(self, violation, frame):
        timestamp = datetime.now().isoformat().replace(':', '-')  # Fix filename
        image_path = f"outputs/violations/{timestamp}.jpg"
        
        os.makedirs('outputs/violations', exist_ok=True)
        
        # Ensure frame is saved successfully
        success = cv2.imwrite(image_path, frame)
        if not success:
            print(f"Failed to save image: {image_path}")
            return
        
        # Enhanced database schema
        self.conn.execute(
            "INSERT INTO violations (timestamp, violation_type, image_path, vehicle_id, location, gps_coords, camera_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (timestamp, 
             f"{violation['type']} ({violation.get('vehicle_type', 'unknown')})", 
             image_path, 
             f"{violation.get('vehicle_type', 'vehicle')}_{violation['frame']}", 
             violation.get('location', 'Unknown Location'), 
             violation.get('gps_coords', '0.0, 0.0'),
             violation.get('camera_id', 'CAM_UNKNOWN'))
        )
        self.conn.commit()
        print(f"Violation saved: {violation['type']} ({violation.get('vehicle_type', 'unknown')}) at {timestamp}")

# Usage
if __name__ == "__main__":
    processor = LocalTrafficProcessor()
    # Check if any sample video exists
    import glob
    sample_videos = glob.glob("data/samples/*.mp4")
    if sample_videos:
        print(f"Processing video: {sample_videos[0]}")
        processor.process_video(sample_videos[0])
    else:
        print("No sample videos found in data/samples/")