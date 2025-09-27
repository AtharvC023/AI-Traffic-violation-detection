import cv2
import pytesseract
import re
import numpy as np

class LicensePlateDetector:
    def __init__(self):
        # Set tesseract path (adjust for your system)
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        pass
    
    def detect_license_plate(self, vehicle_region):
        """Extract license plate from vehicle region"""
        try:
            # Preprocess image for better OCR
            processed = self.preprocess_for_ocr(vehicle_region)
            
            # Extract text using OCR
            text = pytesseract.image_to_string(
                processed, 
                config='--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
            )
            
            # Clean and validate plate number
            plate_number = self.clean_plate_text(text)
            
            if self.is_valid_plate(plate_number):
                return plate_number
            
        except Exception as e:
            print(f"OCR Error: {e}")
        
        return None
    
    def preprocess_for_ocr(self, image):
        """Enhance image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Resize for better OCR
        height, width = processed.shape
        if height < 50:
            scale = 50 / height
            new_width = int(width * scale)
            processed = cv2.resize(processed, (new_width, 50))
        
        return processed
    
    def clean_plate_text(self, text):
        """Clean OCR text to extract plate number"""
        # Remove whitespace and special characters
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        return cleaned
    
    def is_valid_plate(self, plate):
        """Validate if text looks like a license plate"""
        if not plate or len(plate) < 4 or len(plate) > 10:
            return False
        
        # Check for common patterns (adjust for your region)
        patterns = [
            r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$',  # Indian format
            r'^[A-Z]{3}[0-9]{3,4}$',                 # US format
            r'^[A-Z]{2}[0-9]{2}[A-Z]{3}$',          # UK format
            r'^[A-Z0-9]{4,8}$'                       # Generic
        ]
        
        return any(re.match(pattern, plate) for pattern in patterns)
    
    def find_plate_region(self, vehicle_image):
        """Find potential license plate regions in vehicle"""
        gray = cv2.cvtColor(vehicle_image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        plate_regions = []
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by aspect ratio (plates are wider than tall)
            aspect_ratio = w / h
            area = w * h
            
            if (2.0 < aspect_ratio < 6.0 and 
                area > 500 and 
                w > 50 and h > 15):
                
                plate_region = vehicle_image[y:y+h, x:x+w]
                plate_regions.append((plate_region, (x, y, w, h)))
        
        return plate_regions

# Usage example
if __name__ == "__main__":
    detector = LicensePlateDetector()
    
    # Test with a vehicle image
    image = cv2.imread("test_vehicle.jpg")
    if image is not None:
        plate_regions = detector.find_plate_region(image)
        
        for plate_img, bbox in plate_regions:
            plate_number = detector.detect_license_plate(plate_img)
            if plate_number:
                print(f"Detected plate: {plate_number}")