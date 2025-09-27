import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import tempfile
import time

class RealTimeVideoProcessor:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        
    def process_frame_with_overlay(self, frame):
        """Process frame and add violation detection overlay"""
        results = self.model(frame)
        
        # Draw detections
        annotated_frame = frame.copy()
        violations = []
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                conf = float(box.conf)
                cls = int(box.cls)
                
                # Draw bounding boxes
                if cls == 2:  # car
                    color = (0, 255, 0)  # Green for cars
                    label = f"Car {conf:.2f}"
                    
                    # Check for violations
                    car_y = y2
                    frame_height = frame.shape[0]
                    
                    # If car in intersection area (bottom 30%)
                    if car_y > frame_height * 0.7:
                        color = (0, 0, 255)  # Red for violation
                        label = "🚨 VIOLATION: Red Light"
                        violations.append({
                            'type': 'red_light_violation',
                            'bbox': [x1, y1, x2, y2],
                            'confidence': conf
                        })
                        
                        # Add violation alert overlay
                        cv2.rectangle(annotated_frame, (10, 10), (400, 60), (0, 0, 255), -1)
                        cv2.putText(annotated_frame, "🚨 VIOLATION DETECTED!", 
                                  (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(annotated_frame, label, (x1, y1-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                elif cls == 9:  # traffic light
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                    cv2.putText(annotated_frame, f"Traffic Light {conf:.2f}", 
                              (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        return annotated_frame, violations

def main():
    st.title("🎥 Real-Time Traffic Violation Detection")
    
    # Sidebar controls
    st.sidebar.title("Video Controls")
    
    uploaded_file = st.file_uploader("Upload Traffic Video", type=['mp4', 'avi', 'mov'])
    
    if uploaded_file:
        # Save uploaded file temporarily
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name
        
        # Video player controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            play_button = st.button("▶️ Play")
        with col2:
            pause_button = st.button("⏸️ Pause")
        with col3:
            stop_button = st.button("⏹️ Stop")
        
        # Speed control
        speed = st.sidebar.slider("Playback Speed", 0.1, 2.0, 1.0, 0.1)
        
        # Detection settings
        st.sidebar.subheader("Detection Settings")
        show_boxes = st.sidebar.checkbox("Show Detection Boxes", True)
        show_violations_only = st.sidebar.checkbox("Highlight Violations Only", False)
        
        # Video processing
        if play_button or 'playing' not in st.session_state:
            st.session_state.playing = True
            st.session_state.paused = False
        
        if pause_button:
            st.session_state.paused = True
            
        if stop_button:
            st.session_state.playing = False
            st.session_state.paused = False
        
        # Main video display area
        video_placeholder = st.empty()
        stats_placeholder = st.empty()
        violations_placeholder = st.empty()
        
        if st.session_state.get('playing', False) and not st.session_state.get('paused', False):
            processor = RealTimeVideoProcessor()
            cap = cv2.VideoCapture(video_path)
            
            frame_count = 0
            total_violations = 0
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            while cap.isOpened() and st.session_state.get('playing', False):
                if st.session_state.get('paused', False):
                    time.sleep(0.1)
                    continue
                    
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                annotated_frame, violations = processor.process_frame_with_overlay(frame)
                
                # Update violation count
                total_violations += len(violations)
                
                # Display frame
                video_placeholder.image(annotated_frame, channels="BGR", use_column_width=True)
                
                # Display stats
                with stats_placeholder.container():
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Frame", frame_count)
                    with col2:
                        st.metric("Total Violations", total_violations)
                    with col3:
                        st.metric("Current Violations", len(violations))
                    with col4:
                        progress = frame_count / cap.get(cv2.CAP_PROP_FRAME_COUNT)
                        st.metric("Progress", f"{progress:.1%}")
                
                # Display current violations
                if violations:
                    with violations_placeholder.container():
                        st.error("🚨 LIVE VIOLATIONS DETECTED!")
                        for i, violation in enumerate(violations):
                            st.write(f"**Violation {i+1}:** {violation['type']}")
                            st.write(f"**Confidence:** {violation['confidence']:.2f}")
                            st.write(f"**Location:** Frame {frame_count}")
                
                # Control playback speed
                time.sleep((1.0 / fps) / speed)
                frame_count += 1
                
                # Check for stop/pause
                if st.session_state.get('paused', False) or not st.session_state.get('playing', False):
                    break
            
            cap.release()
            
            if frame_count > 0:
                st.success(f"✅ Video processing complete! Found {total_violations} total violations.")
    
    else:
        st.info("👆 Upload a traffic video to start real-time violation detection")
        
        # Demo section
        st.subheader("🎯 What You'll See:")
        st.write("- **Green boxes**: Normal vehicles")
        st.write("- **Red boxes**: Vehicles committing violations")
        st.write("- **Yellow boxes**: Traffic lights")
        st.write("- **Red alert banner**: When violation is detected")
        st.write("- **Live stats**: Frame count, violation count, progress")

if __name__ == "__main__":
    main()