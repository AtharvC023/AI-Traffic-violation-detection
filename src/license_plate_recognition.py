import cv2
import numpy as np
import easyocr
import re
from ultralytics import YOLO

class LicensePlateRecognizer:
    def __init__(self):
        self.reader = easyocr.Reader(['en'])
        self.yolo_model = YOLO('yolov8n.pt')
        
    def detect_license_plates(self, image):
        """Detect license plate regions using YOLO"""
        results = self.yolo_model(image)
        plates = []
        
        if results[0].boxes is not None:
            for box in results[0].boxes:
                # Look for car/vehicle detections
                class_id = int(box.cls[0])
                if class_id in [2, 3, 5, 7]:  # car, motorcycle, bus, truck
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    vehicle_roi = image[y1:y2, x1:x2]
                    
                    # Extract potential plate region (bottom 30% of vehicle)
                    h, w = vehicle_roi.shape[:2]
                    plate_roi = vehicle_roi[int(h*0.7):h, :]
                    
                    plates.append({
                        'roi': plate_roi,
                        'bbox': (x1, int(y1 + h*0.7), x2, y2),
                        'vehicle_bbox': (x1, y1, x2, y2)
                    })
        
        return plates
    
    def preprocess_plate(self, plate_roi):
        """Preprocess plate image for better OCR"""
        if plate_roi.size == 0:
            return None
            
        # Convert to grayscale
        gray = cv2.cvtColor(plate_roi, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Gaussian blur and threshold
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return thresh
    
    def extract_text(self, processed_plate):
        """Extract text from preprocessed plate"""
        if processed_plate is None:
            return ""
            
        try:
            results = self.reader.readtext(processed_plate)
            
            # Combine all detected text
            text = ""
            for (bbox, detected_text, confidence) in results:
                if confidence > 0.5:  # Only high confidence detections
                    text += detected_text + " "
            
            return text.strip()
        except:
            return ""
    
    def clean_plate_text(self, text):
        """Clean and format license plate text"""
        if not text:
            return ""
            
        # Remove special characters and spaces
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        
        # Basic validation (6-8 characters typical for plates)
        if 4 <= len(cleaned) <= 10:
            return cleaned
        
        return ""
    
    def recognize_license_plate(self, image):
        """Main function to recognize license plates"""
        plates_data = []
        
        # Detect potential plate regions
        detected_plates = self.detect_license_plates(image)
        
        for plate_info in detected_plates:
            # Preprocess plate region
            processed = self.preprocess_plate(plate_info['roi'])
            
            # Extract text
            raw_text = self.extract_text(processed)
            
            # Clean text
            plate_number = self.clean_plate_text(raw_text)
            
            if plate_number:
                plates_data.append({
                    'plate_number': plate_number,
                    'bbox': plate_info['bbox'],
                    'vehicle_bbox': plate_info['vehicle_bbox'],
                    'confidence': 0.8,  # Simplified confidence
                    'raw_text': raw_text
                })
        
        return plates_data
    
    def draw_plates(self, image, plates_data):
        """Draw detected plates on image"""
        annotated = image.copy()
        
        for plate in plates_data:
            # Draw vehicle bounding box
            x1, y1, x2, y2 = plate['vehicle_bbox']
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw plate bounding box
            px1, py1, px2, py2 = plate['bbox']
            cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 0, 255), 2)
            
            # Add plate number text
            cv2.putText(annotated, plate['plate_number'], 
                       (px1, py1-10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (0, 0, 255), 2)
        
        return annotated

# Integration function for main dashboard
def process_frame_with_plates(frame, recognizer=None):
    """Process frame and return with plate annotations"""
    if recognizer is None:
        recognizer = LicensePlateRecognizer()
    
    plates = recognizer.recognize_license_plate(frame)
    annotated_frame = recognizer.draw_plates(frame, plates)
    
    return annotated_frame, plates