#!/usr/bin/env python3
"""
Test License Plate Recognition
"""

import cv2
import os
from src.license_plate_recognition import LicensePlateRecognizer

def test_license_plate_recognition():
    """Test license plate recognition on sample images"""
    recognizer = LicensePlateRecognizer()
    sample_dir = "data/samples"
    
    # Get sample images
    image_files = [f for f in os.listdir(sample_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("No sample images found in data/samples/")
        return
    
    print(f"Testing license plate recognition on {len(image_files)} images...")
    
    for image_file in image_files:
        image_path = os.path.join(sample_dir, image_file)
        print(f"\nProcessing: {image_file}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Could not load {image_file}")
            continue
        
        # Recognize license plates
        plates_data = recognizer.recognize_license_plate(image)
        
        if plates_data:
            print(f"Found {len(plates_data)} license plates:")
            for i, plate in enumerate(plates_data, 1):
                print(f"  {i}. Plate: {plate['plate_number']}")
                print(f"     Confidence: {plate['confidence']:.2f}")
                print(f"     Raw text: {plate['raw_text']}")
            
            # Save annotated image
            annotated = recognizer.draw_plates(image, plates_data)
            output_path = f"outputs/violations/plates_{image_file}"
            os.makedirs("outputs/violations", exist_ok=True)
            cv2.imwrite(output_path, annotated)
            print(f"     Saved annotated image: {output_path}")
        else:
            print("  No license plates detected")
    
    print("\nLicense plate recognition test completed!")

if __name__ == "__main__":
    test_license_plate_recognition()