#!/usr/bin/env python3
"""
Standalone script to process traffic images for violations
"""

import os
import sys
import glob
from src.image_processor import ImageViolationProcessor

def main():
    print("🚦 Traffic Violation Image Processor")
    print("=" * 40)
    
    # Check for images in data/samples
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(f"data/samples/{ext}"))
        image_files.extend(glob.glob(f"data/samples/{ext.upper()}"))
    
    if not image_files:
        print("No images found in data/samples/")
        print("Please add some traffic images (.jpg, .png, etc.) to data/samples/")
        return
    
    print(f"Found {len(image_files)} image(s) to process:")
    for img in image_files:
        print(f"  - {os.path.basename(img)}")
    
    # Process images
    processor = ImageViolationProcessor()
    total_violations = 0
    
    os.makedirs('outputs/violations', exist_ok=True)
    
    for image_path in image_files:
        print(f"\nProcessing: {os.path.basename(image_path)}")
        
        output_path = f"outputs/violations/analyzed_{os.path.basename(image_path)}"
        annotated_image, violations = processor.process_image(image_path, output_path)
        
        if violations:
            print(f"  ✅ Found {len(violations)} violation(s):")
            for violation in violations:
                print(f"    - {violation['type'].replace('_', ' ').title()}: {violation['description']}")
            total_violations += len(violations)
        else:
            print("  ✅ No violations detected")
        
        print(f"  📁 Saved annotated image: {output_path}")
    
    print(f"\n🎯 Summary:")
    print(f"  - Images processed: {len(image_files)}")
    print(f"  - Total violations found: {total_violations}")
    print(f"  - Results saved in: outputs/violations/")
    print(f"  - Database updated: current_session.db")

if __name__ == "__main__":
    main()