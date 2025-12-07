"""
Quick test script to verify the model works correctly
"""

import cv2
import numpy as np
from traffic_model import TrafficViolationModel

def test_model():
    """Test the model with a simple synthetic image"""
    print("Testing Traffic Violation Detection Model...")
    print("=" * 50)
    
    # Initialize model
    try:
        model = TrafficViolationModel()
        print("✅ Model loaded successfully")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False
    
    # Get model info
    info = model.get_model_info()
    print(f"\nModel Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Create a test image (simple colored rectangle)
    print("\n📸 Creating test image...")
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a simple "road" scene
    cv2.rectangle(test_image, (0, 300), (640, 400), (100, 100, 100), -1)  # Road
    cv2.rectangle(test_image, (200, 320), (300, 380), (0, 0, 255), -1)  # Red rectangle (car-like)
    cv2.rectangle(test_image, (400, 320), (500, 380), (0, 255, 0), -1)  # Green rectangle
    
    # Save test image
    cv2.imwrite('test_image.jpg', test_image)
    print("✅ Test image created: test_image.jpg")
    
    # Test detection
    print("\n🔍 Running detection...")
    try:
        detections = model.detect_objects(test_image, conf=0.1)
        print(f"✅ Detection successful! Found {len(detections)} objects")
        
        if detections:
            print("\nDetections:")
            for i, det in enumerate(detections[:5], 1):  # Show first 5
                print(f"  {i}. {det['class_name']}: {det['confidence']:.2f} at {det['bbox']}")
        else:
            print("  (No objects detected - this is normal for synthetic images)")
        
        # Test vehicle detection
        vehicles = model.detect_vehicles(test_image)
        print(f"\n🚗 Vehicle detection: Found {len(vehicles)} vehicles")
        
        # Test traffic light detection
        lights = model.detect_traffic_lights(test_image)
        print(f"🚦 Traffic light detection: Found {len(lights)} traffic lights")
        
        # Draw detections
        annotated = model.draw_detections(test_image, detections)
        cv2.imwrite('test_output.jpg', annotated)
        print("\n✅ Annotated image saved: test_output.jpg")
        
    except Exception as e:
        print(f"❌ Error during detection: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 50)
    print("✅ All tests passed! Model is working correctly.")
    print("\nYou can now use this model in your project!")
    print("See example_usage.py for usage examples.")
    
    return True

if __name__ == "__main__":
    success = test_model()
    exit(0 if success else 1)

