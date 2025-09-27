import cv2
import sqlite3
from ultralytics import YOLO
from datetime import datetime
import os
import numpy as np

class ImageViolationProcessor:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.setup_database()
        
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
        
    def process_image(self, image_path, output_path=None):
        """Process single image and detect violations"""
        image = cv2.imread(image_path)
        if image is None:
            return None, []
            
        violations = self.detect_violations_in_image(image)
        annotated_image = self.draw_violations(image.copy(), violations)
        
        if output_path:
            cv2.imwrite(output_path, annotated_image)
            
        # Save violations to database
        for violation in violations:
            self.save_violation(violation, annotated_image, image_path)
            
        return annotated_image, violations
    
    def detect_violations_in_image(self, image):
        """Detect all violations in a single image"""
        results = self.model(image, conf=0.25)
        violations = []
        
        vehicles = {'cars': [], 'motorcycles': [], 'buses': [], 'trucks': []}
        traffic_lights = []
        persons = []
        
        # COCO class mapping
        vehicle_classes = {2: 'cars', 3: 'motorcycles', 5: 'buses', 7: 'trucks'}
        
        for r in results:
            for box in r.boxes:
                cls = int(box.cls)
                bbox = box.xyxy[0].tolist()
                conf = float(box.conf)
                
                if cls in vehicle_classes and self.is_valid_vehicle(bbox, conf, cls):
                    vehicles[vehicle_classes[cls]].append({
                        'bbox': bbox, 'confidence': conf, 'type': vehicle_classes[cls][:-1]
                    })
                elif cls == 9:  # traffic light
                    traffic_lights.append({'bbox': bbox, 'confidence': conf})
                elif cls == 0:  # person
                    persons.append({'bbox': bbox, 'confidence': conf})
        
        # Check violations
        violations.extend(self.check_red_light_violations(image, vehicles, traffic_lights))
        violations.extend(self.check_helmet_violations(image, vehicles['motorcycles'], persons))
        violations.extend(self.check_lane_violations(image, vehicles))
        violations.extend(self.check_crosswalk_violations(image, vehicles, persons))
        violations.extend(self.check_parking_violations(image, vehicles))
        
        return violations
    
    def check_red_light_violations(self, image, vehicles, traffic_lights):
        """Check for red light violations"""
        violations = []
        red_light_detected = self.detect_red_light(image, traffic_lights)
        
        if red_light_detected:
            frame_height = image.shape[0]
            for vehicle_type, vehicle_list in vehicles.items():
                for vehicle in vehicle_list:
                    vehicle_y = vehicle['bbox'][3]
                    if vehicle_y > frame_height * 0.7:  # In intersection
                        violations.append({
                            'type': 'red_light_violation',
                            'vehicle_type': vehicle['type'],
                            'bbox': vehicle['bbox'],
                            'confidence': vehicle['confidence'],
                            'description': f"{vehicle['type'].title()} running red light"
                        })
        return violations
    
    def check_helmet_violations(self, image, motorcycles, persons):
        """Check for helmet violations"""
        violations = []
        for motorcycle in motorcycles:
            mx1, my1, mx2, my2 = motorcycle['bbox']
            
            for person in persons:
                px1, py1, px2, py2 = person['bbox']
                
                # Check overlap
                if (px1 < mx2 and px2 > mx1 and py1 < my2 and py2 > my1):
                    # Simple helmet detection
                    head_height = int((py2 - py1) * 0.2)
                    head_region = image[int(py1):int(py1 + head_height), int(px1):int(px2)]
                    
                    if head_region.size > 0:
                        gray = cv2.cvtColor(head_region, cv2.COLOR_BGR2GRAY)
                        mask = (gray < 80).astype('uint8')
                        dark_pixels = cv2.countNonZero(mask)
                        total_pixels = gray.shape[0] * gray.shape[1]
                        
                        if dark_pixels < total_pixels * 0.3:
                            violations.append({
                                'type': 'no_helmet_violation',
                                'vehicle_type': 'motorcycle',
                                'bbox': motorcycle['bbox'],
                                'confidence': motorcycle['confidence'],
                                'description': 'Motorcycle rider without helmet'
                            })
                            break
        return violations
    
    def check_lane_violations(self, image, vehicles):
        """Check for lane violations"""
        violations = []
        frame_width = image.shape[1]
        center_line = frame_width // 2
        
        for vehicle_type, vehicle_list in vehicles.items():
            for vehicle in vehicle_list:
                vx1, vy1, vx2, vy2 = vehicle['bbox']
                vehicle_center_x = (vx1 + vx2) / 2
                
                # Check if crossing center line
                if abs(vehicle_center_x - center_line) < 50:
                    violations.append({
                        'type': 'lane_violation',
                        'vehicle_type': vehicle['type'],
                        'bbox': vehicle['bbox'],
                        'confidence': vehicle['confidence'],
                        'description': f"{vehicle['type'].title()} crossing lane markings"
                    })
        return violations
    
    def check_crosswalk_violations(self, image, vehicles, persons):
        """Check for crosswalk violations"""
        violations = []
        frame_height = image.shape[0]
        crosswalk_y1 = int(frame_height * 0.4)
        crosswalk_y2 = int(frame_height * 0.6)
        
        # Check if pedestrians in crosswalk
        pedestrians_in_crosswalk = any(
            crosswalk_y1 < person['bbox'][3] < crosswalk_y2 for person in persons
        )
        
        if pedestrians_in_crosswalk:
            for vehicle_type, vehicle_list in vehicles.items():
                for vehicle in vehicle_list:
                    vy2 = vehicle['bbox'][3]
                    if crosswalk_y1 < vy2 < crosswalk_y2:
                        violations.append({
                            'type': 'crosswalk_violation',
                            'vehicle_type': vehicle['type'],
                            'bbox': vehicle['bbox'],
                            'confidence': vehicle['confidence'],
                            'description': f"{vehicle['type'].title()} not yielding to pedestrians"
                        })
        return violations
    
    def check_parking_violations(self, image, vehicles):
        """Check for parking violations (vehicles in roadway)"""
        violations = []
        frame_height = image.shape[0]
        
        for vehicle_type, vehicle_list in vehicles.items():
            for vehicle in vehicle_list:
                vy2 = vehicle['bbox'][3]
                # If vehicle in main roadway area
                if vy2 > frame_height * 0.3:
                    violations.append({
                        'type': 'potential_parking_violation',
                        'vehicle_type': vehicle['type'],
                        'bbox': vehicle['bbox'],
                        'confidence': vehicle['confidence'],
                        'description': f"{vehicle['type'].title()} potentially parked in roadway"
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
        min_confidence = {2: 0.4, 3: 0.35, 5: 0.5, 7: 0.45}
        
        if confidence < min_confidence.get(vehicle_class, 0.3):
            return False
        
        # Size and shape filters
        if area < 1000 or area > 200000 or width < 30 or height < 30:
            return False
        
        # Aspect ratio filters by vehicle type
        if vehicle_class == 2 and (aspect_ratio < 0.8 or aspect_ratio > 3.0):
            return False
        elif vehicle_class == 3 and (aspect_ratio < 0.3 or aspect_ratio > 2.5):
            return False
        elif vehicle_class in [5, 7] and (aspect_ratio < 0.5 or aspect_ratio > 4.0):
            return False
        
        # Reject zebra crossings and lane markings
        if aspect_ratio > 5.0 or aspect_ratio < 0.2:
            return False
            
        return True
    
    def detect_red_light(self, image, traffic_lights):
        """Detect red traffic lights"""
        for light in traffic_lights:
            x1, y1, x2, y2 = [int(coord) for coord in light['bbox']]
            light_region = image[y1:y2, x1:x2]
            
            if light_region.size > 0:
                hsv = cv2.cvtColor(light_region, cv2.COLOR_BGR2HSV)
                
                # Red color masks
                lower_red1, upper_red1 = (0, 50, 50), (10, 255, 255)
                lower_red2, upper_red2 = (170, 50, 50), (180, 255, 255)
                
                mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                red_mask = mask1 + mask2
                
                red_pixels = cv2.countNonZero(red_mask)
                total_pixels = light_region.shape[0] * light_region.shape[1]
                
                if red_pixels > total_pixels * 0.1:
                    return True
        return False
    
    def draw_violations(self, image, violations):
        """Draw violation annotations on image"""
        colors = {
            'red_light_violation': (0, 0, 255),
            'no_helmet_violation': (255, 0, 255),
            'lane_violation': (0, 255, 255),
            'crosswalk_violation': (255, 255, 0),
            'potential_parking_violation': (128, 128, 128)
        }
        
        for violation in violations:
            bbox = violation['bbox']
            x1, y1, x2, y2 = [int(coord) for coord in bbox]
            color = colors.get(violation['type'], (0, 255, 0))
            
            # Draw rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 3)
            
            # Draw label
            label = f"🚨 {violation['type'].replace('_', ' ').upper()}"
            cv2.putText(image, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return image
    
    def save_violation(self, violation, annotated_image, original_path):
        """Save violation to database"""
        timestamp = datetime.now().isoformat().replace(':', '-')
        image_name = f"violation_{timestamp}.jpg"
        image_path = f"outputs/violations/{image_name}"
        
        os.makedirs('outputs/violations', exist_ok=True)
        cv2.imwrite(image_path, annotated_image)
        
        self.conn.execute(
            "INSERT INTO violations (timestamp, violation_type, image_path, vehicle_id, location, gps_coords, camera_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (timestamp, 
             f"{violation['type']} ({violation['vehicle_type']})", 
             image_path, 
             f"{violation['vehicle_type']}_static", 
             f"Image: {os.path.basename(original_path)}", 
             "0.0, 0.0",
             "IMG_UPLOAD")
        )
        self.conn.commit()