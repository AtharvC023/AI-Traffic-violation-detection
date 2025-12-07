"""
Example usage of the Traffic Violation Detection Model
"""

import cv2
import numpy as np
from traffic_model import TrafficViolationModel, load_model


def example_1_image_detection():
    """Example 1: Detect objects in a single image"""
    print("\n=== Example 1: Image Detection ===")
    
    # Initialize model
    model = load_model()
    
    # Load image
    image_path = 'your_image.jpg'  # Replace with your image path
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Could not load image: {image_path}")
        return
    
    # Detect objects
    detections = model.detect_objects(image, conf=0.25)
    
    print(f"Found {len(detections)} objects:")
    for det in detections:
        print(f"  - {det['class_name']}: {det['confidence']:.2f} at {det['bbox']}")
    
    # Draw detections
    annotated = model.draw_detections(image, detections)
    
    # Save or display
    cv2.imwrite('output_detections.jpg', annotated)
    print("Saved annotated image to: output_detections.jpg")


def example_2_vehicle_detection():
    """Example 2: Detect only vehicles"""
    print("\n=== Example 2: Vehicle Detection ===")
    
    model = load_model()
    image = cv2.imread('your_image.jpg')  # Replace with your image
    
    if image is None:
        print("Could not load image")
        return
    
    # Detect only vehicles
    vehicles = model.detect_vehicles(image)
    
    print(f"Found {len(vehicles)} vehicles:")
    for vehicle in vehicles:
        print(f"  - {vehicle['vehicle_type']}: {vehicle['confidence']:.2f}")
    
    # Draw vehicles
    annotated = model.draw_detections(image, vehicles)
    cv2.imwrite('output_vehicles.jpg', annotated)


def example_3_traffic_light_detection():
    """Example 3: Detect traffic lights and their colors"""
    print("\n=== Example 3: Traffic Light Detection ===")
    
    model = load_model()
    image = cv2.imread('your_image.jpg')  # Replace with your image
    
    if image is None:
        print("Could not load image")
        return
    
    # Detect traffic lights
    lights = model.detect_traffic_lights(image)
    
    print(f"Found {len(lights)} traffic lights:")
    for light in lights:
        print(f"  - Color: {light['color']}, Confidence: {light['confidence']:.2f}")
    
    # Draw traffic lights
    annotated = model.draw_detections(image, lights)
    cv2.imwrite('output_traffic_lights.jpg', annotated)


def example_4_video_processing():
    """Example 4: Process a video file"""
    print("\n=== Example 4: Video Processing ===")
    
    model = load_model()
    video_path = 'your_video.mp4'  # Replace with your video path
    
    # Process video (every 5th frame for speed)
    model.process_video(
        video_path, 
        output_path='output_video.mp4',
        frame_skip=5,  # Process every 5th frame
        show_preview=False
    )
    
    print("Video processing complete! Output saved to: output_video.mp4")


def example_5_real_time_detection():
    """Example 5: Real-time detection from webcam"""
    print("\n=== Example 5: Real-time Detection ===")
    
    model = load_model()
    cap = cv2.VideoCapture(0)  # 0 = default camera
    
    if not cap.isOpened():
        print("Could not open camera")
        return
    
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect objects
        detections = model.detect_objects(frame, conf=0.3)
        
        # Draw detections
        annotated = model.draw_detections(frame, detections)
        
        # Add FPS and count
        cv2.putText(annotated, f"Detections: {len(detections)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display
        cv2.imshow('Real-time Detection', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()


def example_6_custom_violation_detection():
    """Example 6: Custom violation detection logic"""
    print("\n=== Example 6: Custom Violation Detection ===")
    
    model = load_model()
    image = cv2.imread('your_image.jpg')  # Replace with your image
    
    if image is None:
        print("Could not load image")
        return
    
    # Detect all objects
    detections = model.detect_objects(image)
    
    # Custom logic: Check for red light violation
    vehicles = model.detect_vehicles(image)
    traffic_lights = model.detect_traffic_lights(image)
    
    # Check if red light and vehicle in intersection
    red_light_detected = any(light['color'] == 'red' for light in traffic_lights)
    
    violations = []
    if red_light_detected:
        frame_height = image.shape[0]
        for vehicle in vehicles:
            # If vehicle is in intersection (bottom 30% of frame)
            if vehicle['bbox'][3] > frame_height * 0.7:
                violations.append({
                    'type': 'red_light_violation',
                    'vehicle': vehicle['vehicle_type'],
                    'confidence': vehicle['confidence']
                })
    
    print(f"Found {len(violations)} violations:")
    for violation in violations:
        print(f"  - {violation['type']}: {violation['vehicle']}")
    
    # Draw violations
    all_detections = vehicles + traffic_lights
    annotated = model.draw_detections(image, all_detections)
    
    # Highlight violations
    for violation in violations:
        # Find corresponding vehicle
        for vehicle in vehicles:
            if vehicle['vehicle_type'] == violation['vehicle']:
                x1, y1, x2, y2 = vehicle['bbox']
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 4)
                cv2.putText(annotated, "VIOLATION", (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                break
    
    cv2.imwrite('output_violations.jpg', annotated)
    print("Saved violation detection to: output_violations.jpg")


def example_7_model_info():
    """Example 7: Get model information"""
    print("\n=== Example 7: Model Information ===")
    
    model = load_model()
    info = model.get_model_info()
    
    print("Model Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    print("Traffic Violation Detection Model - Usage Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run:
    
    # example_1_image_detection()
    # example_2_vehicle_detection()
    # example_3_traffic_light_detection()
    # example_4_video_processing()
    # example_5_real_time_detection()
    # example_6_custom_violation_detection()
    example_7_model_info()
    
    print("\n" + "=" * 50)
    print("Examples complete! Modify the code to use your own images/videos.")

