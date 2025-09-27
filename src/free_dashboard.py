import streamlit as st
import sqlite3
import pandas as pd
import cv2
import os
import shutil
from PIL import Image
from datetime import datetime

st.set_page_config(
    page_title="AI Traffic Monitor",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set dark theme
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background-color: #0f172a;
    }
    [data-testid="stHeader"] {
        background-color: #0f172a;
    }
    [data-testid="stSidebar"] {
        background-color: #1e293b;
    }
</style>
""", unsafe_allow_html=True)

# Modern Dark Theme CSS styling
st.markdown("""
<style>
    /* Global dark theme */
    .main {
        background-color: #0f172a;
        color: #e2e8f0;
    }

    /* Main header with dark gradient */
    .main-header {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        padding: 2rem;
        border-radius: 15px;
        color: #f1f5f9;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border: 1px solid #334155;
    }

    /* Metric cards with dark theme */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        border-left: 4px solid #3b82f6;
        border: 1px solid #475569;
        color: #f1f5f9;
    }

    /* Violation cards */
    .violation-card {
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
        border: 1px solid #dc2626;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #fef2f2;
        box-shadow: 0 4px 16px rgba(220, 38, 38, 0.2);
    }

    /* Success cards */
    .success-card {
        background: linear-gradient(135deg, #14532d 0%, #166534 100%);
        border: 1px solid #16a34a;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #f0fdf4;
        box-shadow: 0 4px 16px rgba(22, 163, 74, 0.2);
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid #334155;
    }

    /* Buttons with modern dark theme */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.4);
        background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
    }

    /* Upload section */
    .upload-section {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 2px dashed #64748b;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        color: #cbd5e1;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }

    /* Stats container */
    .stats-container {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        margin: 1rem 0;
        border: 1px solid #475569;
        color: #e2e8f0;
    }

    /* Streamlit specific overrides */
    .stTextInput > div > div > input {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #475569;
        border-radius: 8px;
    }

    .stSelectbox > div > div > div {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #475569;
    }

    .stSlider > div > div > div > div {
        background-color: #3b82f6;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #3b82f6;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 0.5rem;
    }

    .stTabs [data-baseweb="tab"] {
        color: #cbd5e1;
        border-radius: 8px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #3b82f6;
        color: white;
    }

    /* Dataframe styling */
    .stDataFrame {
        background-color: #1e293b;
        border-radius: 10px;
        border: 1px solid #475569;
    }

    .stDataFrame th {
        background-color: #334155;
        color: #f1f5f9;
    }

    .stDataFrame td {
        color: #e2e8f0;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1e293b;
        color: #e2e8f0;
        border: 1px solid #475569;
        border-radius: 8px;
    }

    /* Metric text */
    .css-1xarl3l {
        color: #e2e8f0;
    }

    /* Sidebar text */
    .sidebar .sidebar-content .css-1lcbmhc {
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

def detect_traffic_light_color(light_region):
    """Improved traffic light color detection"""
    if light_region.size == 0:
        return False, False, False
    
    hsv = cv2.cvtColor(light_region, cv2.COLOR_BGR2HSV)
    total_pixels = light_region.shape[0] * light_region.shape[1]
    
    # Red detection (improved ranges)
    lower_red1, upper_red1 = (0, 120, 70), (10, 255, 255)
    lower_red2, upper_red2 = (170, 120, 70), (180, 255, 255)
    red_mask = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
    red_pixels = cv2.countNonZero(red_mask)
    
    # Yellow detection
    lower_yellow, upper_yellow = (15, 120, 70), (35, 255, 255)
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    yellow_pixels = cv2.countNonZero(yellow_mask)
    
    # Green detection
    lower_green, upper_green = (40, 120, 70), (80, 255, 255)
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_pixels = cv2.countNonZero(green_mask)
    
    # Determine dominant color (minimum 8% threshold)
    threshold = total_pixels * 0.08
    
    is_red = red_pixels > threshold
    is_yellow = yellow_pixels > threshold
    is_green = green_pixels > threshold
    
    return is_red, is_yellow, is_green

def is_valid_vehicle_detection(bbox, confidence, vehicle_class):
    """Validate vehicle detection to prevent false positives"""
    x1, y1, x2, y2 = bbox
    width = x2 - x1
    height = y2 - y1
    area = width * height
    aspect_ratio = width / height if height > 0 else 0
    
    # Higher confidence thresholds
    min_confidence = {2: 0.4, 3: 0.35, 5: 0.5, 7: 0.45}
    if confidence < min_confidence.get(vehicle_class, 0.3):
        return False
    
    # Size and shape validation
    if area < 1000 or width < 30 or height < 30:
        return False
    
    # Reject zebra crossings and markings
    if aspect_ratio > 5.0 or aspect_ratio < 0.2:
        return False
        
    return True

def load_violations():
    conn = sqlite3.connect('current_session.db')
    try:
        df = pd.read_sql_query("SELECT * FROM violations ORDER BY timestamp DESC", conn)
    except pd.errors.DatabaseError:
        # Create fresh table for new session
        conn.execute('''
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
        conn.commit()
        df = pd.DataFrame(columns=['id', 'timestamp', 'violation_type', 'image_path', 'vehicle_id', 'location', 'gps_coords', 'camera_id'])
    conn.close()
    return df

def save_violation_to_db(violation_type, vehicle_id, image_path=None, location="Live Detection", gps_coords="0.0,0.0", camera_id="Live Camera"):
    """Save a violation to the database"""
    conn = sqlite3.connect('current_session.db')
    try:
        # Ensure table exists
        conn.execute('''
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

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO violations (timestamp, violation_type, image_path, vehicle_id, location, gps_coords, camera_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, violation_type, image_path or '', vehicle_id, location, gps_coords, camera_id))
        conn.commit()
    except Exception as e:
        st.error(f"Error saving violation to database: {e}")
    finally:
        conn.close()

def main():
    # Modern header
    st.markdown("""
    <div class="main-header">
        <h1>🚦 AI Traffic Monitor</h1>
        <p>Advanced Traffic Violation Detection System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Modern sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; color: #f1f5f9;">
            <h2>🎛️ Control Panel</h2>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.selectbox(
            "📍 Navigate to:",
            ["📊 Dashboard", "📊 Analytics", "🎥 Process Video", "📷 Process Images", "🚨 View Violations", "📺 Live Detection", "🗄️ Archive History"],
            index=0
        )
    
        st.markdown("---")
        st.markdown("### ⚙️ System Controls")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Data", use_container_width=True):
                if os.path.exists('current_session.db'):
                    os.remove('current_session.db')
                if os.path.exists('outputs/violations'):
                    for file in os.listdir('outputs/violations'):
                        if file.endswith('.jpg'):
                            os.remove(f'outputs/violations/{file}')
                st.success("✅ Data cleared!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # System info
        st.markdown("---")
        st.markdown("### 📈 System Status")
        df = load_violations()
        st.metric("Total Records", len(df))
        st.metric("Session Active", "✅ Online")
    
    if page == "📊 Dashboard":
        st.markdown("## 📊 Analytics Dashboard")
        
        df = load_violations()
        
        if not df.empty:
            # Key metrics with modern cards
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h3>🚨 Total Violations</h3>
                    <h2 style="color: #ef4444;">{}</h2>
                </div>
                """.format(len(df)), unsafe_allow_html=True)

            with col2:
                today_count = len(df[df['timestamp'].str.contains(pd.Timestamp.now().strftime('%Y-%m-%d'))])
                st.markdown("""
                <div class="metric-card">
                    <h3>📅 Today's Count</h3>
                    <h2 style="color: #3b82f6;">{}</h2>
                </div>
                """.format(today_count), unsafe_allow_html=True)

            with col3:
                most_common = df['violation_type'].mode().iloc[0] if not df.empty else "None"
                st.markdown("""
                <div class="metric-card">
                    <h3>🔥 Most Common</h3>
                    <h2 style="color: #10b981;">{}</h2>
                </div>
                """.format(most_common.split('(')[0] if '(' in most_common else most_common), unsafe_allow_html=True)

            with col4:
                unique_locations = df['location'].nunique() if 'location' in df.columns else 1
                st.markdown("""
                <div class="metric-card">
                    <h3>📍 Locations</h3>
                    <h2 style="color: #8b5cf6;">{}</h2>
                </div>
                """.format(unique_locations), unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Recent violations with modern styling
            st.markdown("""
            <div class="stats-container">
                <h3>📋 Recent Violations</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display recent violations in cards
            for _, row in df.head(5).iterrows():
                violation_type = row['violation_type'].split('(')[0].strip()
                timestamp = row['timestamp'][:19] if len(row['timestamp']) > 19 else row['timestamp']
                
                st.markdown("""
                <div class="violation-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="margin: 0; color: #fca5a5;">🚨 {}</h4>
                            <p style="margin: 0; color: #fecaca;">📅 {}</p>
                        </div>
                        <div style="text-align: right;">
                            <p style="margin: 0; font-weight: bold; color: #fef2f2;">🚗 {}</p>
                            <p style="margin: 0; color: #fecaca;">📍 {}</p>
                        </div>
                    </div>
                </div>
                """.format(
                    violation_type,
                    timestamp,
                    row.get('vehicle_id', 'Unknown'),
                    row.get('location', 'Unknown')
                ), unsafe_allow_html=True)
        
        else:
            st.markdown("""
            <div class="success-card">
                <h3 style="color: #bbf7d0;">✅ No Violations Detected</h3>
                <p style="color: #d1fae5;">Great! No traffic violations have been recorded yet. Upload a video or image to start monitoring.</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif page == "📊 Analytics":
        from modern_dashboard import show_advanced_analytics, show_system_health
        
        tab1, tab2 = st.tabs(["📊 Analytics", "🔧 System Health"])
        
        with tab1:
            show_advanced_analytics()
        
        with tab2:
            show_system_health()
    
    elif page == "🎥 Process Video":
        st.markdown("## 🎥 Video Analysis")
        
        st.markdown("""
        <div class="upload-section">
            <h3>📤 Upload Traffic Video</h3>
            <p>Supported formats: MP4, AVI, MOV</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose video file", 
            type=['mp4', 'avi', 'mov'],
            help="Upload traffic videos for violation detection"
        )
        
        if uploaded_file:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.video(uploaded_file)
            
            with col2:
                st.markdown("""
                <div class="stats-container">
                    <h4>📊 File Info</h4>
                    <p><strong>Name:</strong> {}</p>
                    <p><strong>Size:</strong> {:.2f} MB</p>
                </div>
                """.format(uploaded_file.name, uploaded_file.size / 1024 / 1024), unsafe_allow_html=True)
                
                if st.button("🚀 Start Analysis", use_container_width=True):
                    with st.spinner("🔄 Analyzing video..."):
                        with open(f"data/samples/{uploaded_file.name}", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        from local_processor import LocalTrafficProcessor
                        processor = LocalTrafficProcessor()
                        processor.process_video(f"data/samples/{uploaded_file.name}")
                    
                    st.success("✅ Analysis complete!")
                    st.balloons()
                    st.rerun()
    
    elif page == "📷 Process Images":
        st.markdown("## 📷 Image Analysis")
        
        st.markdown("""
        <div class="upload-section">
            <h3>📤 Upload Traffic Images</h3>
            <p>Supported formats: JPG, JPEG, PNG, BMP</p>
            <p>Multiple files supported</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose image files", 
            type=['jpg', 'jpeg', 'png', 'bmp'], 
            accept_multiple_files=True,
            help="Upload traffic images for violation detection"
        )
        
        if uploaded_files:
            st.markdown("""
            <div class="success-card">
                <h4>✅ {} Image(s) Uploaded</h4>
                <p>Ready for analysis</p>
            </div>
            """.format(len(uploaded_files)), unsafe_allow_html=True)
            
            # Show image previews
            cols = st.columns(min(len(uploaded_files), 4))
            for i, uploaded_file in enumerate(uploaded_files[:4]):
                with cols[i]:
                    st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)
            
            if len(uploaded_files) > 4:
                st.info(f"... and {len(uploaded_files) - 4} more images")
            
            if st.button("🔍 Analyze All Images", use_container_width=True):
                from image_processor import ImageViolationProcessor
                processor = ImageViolationProcessor()
                
                results = []
                progress_bar = st.progress(0)
                
                for i, uploaded_file in enumerate(uploaded_files):
                    # Save uploaded file
                    input_path = f"data/samples/{uploaded_file.name}"
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process image
                    output_path = f"outputs/violations/analyzed_{uploaded_file.name}"
                    annotated_image, violations = processor.process_image(input_path, output_path)
                    
                    results.append({
                        'filename': uploaded_file.name,
                        'violations': violations,
                        'annotated_image': annotated_image,
                        'output_path': output_path
                    })
                    
                    progress_bar.progress((i + 1) / len(uploaded_files))
                
                st.success(f"✅ Processed {len(uploaded_files)} images!")
                
                # Display results
                total_violations = sum(len(result['violations']) for result in results)
                st.metric("Total Violations Found", total_violations)
                
                for result in results:
                    with st.expander(f"📷 {result['filename']} - {len(result['violations'])} violations", expanded=True):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            if result['annotated_image'] is not None:
                                st.image(result['annotated_image'], 
                                        caption=f"Analyzed: {result['filename']}", 
                                        channels="BGR", 
                                        use_container_width=True)
                        
                        with col2:
                            st.subheader("🚨 Violations Detected")
                            if result['violations']:
                                for i, violation in enumerate(result['violations'], 1):
                                    st.write(f"**{i}. {violation['type'].replace('_', ' ').title()}**")
                                    st.write(f"Vehicle: {violation['vehicle_type'].title()}")
                                    st.write(f"Confidence: {violation['confidence']:.1%}")
                                    st.write(f"Description: {violation['description']}")
                                    st.write("---")
                            else:
                                st.info("No violations detected in this image")
                
                st.rerun()
        
        else:
            st.markdown("""
            <div class="success-card">
                <h3>📸 Image Analysis Capabilities</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                    <div>
                        <h4>🚨 Detectable Violations:</h4>
                        <ul>
                            <li>Red Light Running</li>
                            <li>No Helmet Usage</li>
                            <li>Lane Violations</li>
                            <li>Crosswalk Violations</li>
                            <li>Illegal Parking</li>
                        </ul>
                    </div>
                    <div>
                        <h4>📊 Analysis Features:</h4>
                        <ul>
                            <li>Batch Processing</li>
                            <li>Visual Annotations</li>
                            <li>Confidence Scores</li>
                            <li>Detailed Reports</li>
                            <li>Export Results</li>
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    elif page == "🚨 View Violations":
        st.markdown("## 🚨 Violation Details")
        
        df = load_violations()
        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"{row['violation_type']} - {row['timestamp']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if os.path.exists(row['image_path']):
                            image = Image.open(row['image_path'])
                            st.image(image, caption="Violation Evidence")
                    
                    with col2:
                        st.write(f"**Type:** {row['violation_type']}")
                        st.write(f"**Time:** {row['timestamp']}")
                        st.write(f"**Vehicle ID:** {row['vehicle_id']}")
                        if len(row) > 5:  # Check if location columns exist
                            st.write(f"**📍 Location:** {row.get('location', 'Unknown')}")
                            st.write(f"**🗺️ GPS:** {row.get('gps_coords', 'N/A')}")
                            st.write(f"**📹 Camera:** {row.get('camera_id', 'Unknown')}")
                            
                            # Add Google Maps link
                            if row.get('gps_coords') and row.get('gps_coords') != '0.0, 0.0':
                                maps_url = f"https://maps.google.com/?q={row['gps_coords']}"
                                st.markdown(f"[🗺️ View on Google Maps]({maps_url})")
    
    elif page == "📺 Live Detection":
        st.markdown("## 📺 Live Detection System")
        
        st.markdown("""
        <div class="upload-section">
            <h3>🎥 Live Analysis Setup</h3>
            <p>Upload a video for real-time violation detection</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose video for live analysis", 
            type=['mp4', 'avi', 'mov'],
            help="Real-time processing with violation alerts"
        )
        
        if uploaded_file:
            import tempfile
            import time
            from ultralytics import YOLO
            
            # Save uploaded file
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            tfile.write(uploaded_file.read())
            video_path = tfile.name
            
            # Modern control panel
            st.markdown("""
            <div class="stats-container">
                <h4>🎮 Control Panel</h4>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("▶️ Start Detection", use_container_width=True):
                    st.session_state.start_detection = True
                    st.session_state.stop_detection = False
            with col2:
                if st.button("⏹️ Stop Analysis", use_container_width=True):
                    st.session_state.start_detection = False
                    st.session_state.stop_detection = True
            with col3:
                speed = st.slider("🏃 Speed (FPS)", 1, 30, 10, help="Processing speed")
            with col4:
                max_frames = st.number_input("🎬 Max Frames", 0, 1000, 0, help="0 = Full video")
                if max_frames == 0:
                    max_frames = 999999
            
            # Modern video display layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("""
                <div class="stats-container">
                    <h4>📺 Live Video Feed</h4>
                </div>
                """, unsafe_allow_html=True)
                video_placeholder = st.empty()
                stats_placeholder = st.empty()
            
            with col2:
                st.markdown("""
                <div class="stats-container">
                    <h4>🚨 Live Violations</h4>
                </div>
                """, unsafe_allow_html=True)
                violations_placeholder = st.empty()
            
            if st.session_state.get('start_detection', False):
                model = YOLO('yolov8n.pt')
                cap = cv2.VideoCapture(video_path)
                
                frame_count = 0
                violations_found = 0
                live_violations = []
                violated_vehicles = set()  # Track vehicles that already have violations
                
                progress_bar = st.progress(0)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                
                while cap.isOpened() and frame_count < min(max_frames, total_frames):
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Run detection with lower confidence for traffic lights
                    results = model(frame, conf=0.3)  # Lower threshold
                    annotated_frame = frame.copy()
                    
                    # Draw detections and check violations
                    current_violations = 0
                    traffic_lights = []
                    vehicles = {'cars': [], 'motorcycles': [], 'buses': [], 'trucks': []}
                    persons = []
                    
                    # COCO class mapping
                    vehicle_classes = {
                        2: ('cars', 'Car', (0, 255, 0)),
                        3: ('motorcycles', 'Motorcycle', (255, 0, 255)),
                        5: ('buses', 'Bus', (0, 255, 255)),
                        7: ('trucks', 'Truck', (255, 255, 0))
                    }
                    
                    for r in results:
                        for box in r.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].int().tolist()
                            conf = float(box.conf)
                            cls = int(box.cls)
                            
                            if cls in vehicle_classes and is_valid_vehicle_detection([x1, y1, x2, y2], conf, cls):
                                vehicle_type, label, default_color = vehicle_classes[cls]
                                vehicles[vehicle_type].append((x1, y1, x2, y2, conf))
                                
                                # Default green color for normal vehicles
                                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), default_color, 2)
                                cv2.putText(annotated_frame, f"{label} {conf:.2f}", (x1, y1-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, default_color, 2)
                            
                            elif cls == 0:  # person
                                persons.append((x1, y1, x2, y2, conf))
                                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 1)
                                cv2.putText(annotated_frame, "Person", (x1, y1-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                            
                            elif cls == 9:  # traffic light
                                light_region = frame[y1:y2, x1:x2]
                                is_red, is_yellow, is_green = detect_traffic_light_color(light_region)
                                
                                if is_red:
                                    color = (0, 0, 255)
                                    label = "🔴 RED"
                                    traffic_lights.append((x1, y1, x2, y2, conf, 'red'))
                                elif is_yellow:
                                    color = (0, 255, 255)
                                    label = "🟡 YELLOW"
                                    traffic_lights.append((x1, y1, x2, y2, conf, 'yellow'))
                                elif is_green:
                                    color = (0, 255, 0)
                                    label = "🟢 GREEN"
                                    traffic_lights.append((x1, y1, x2, y2, conf, 'green'))
                                else:
                                    color = (128, 128, 128)
                                    label = "⚪ SIGNAL"
                                    traffic_lights.append((x1, y1, x2, y2, conf, 'unknown'))
                                
                                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 3)
                                cv2.putText(annotated_frame, label, (x1, y1-10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    # Check helmet violations for motorcycles
                    for mx1, my1, mx2, my2, mconf in vehicles['motorcycles']:
                        # Create unique vehicle ID based on position
                        vehicle_id = f"bike_{int(mx1/50)}_{int(my1/50)}"
                        
                        # Skip if this vehicle already has a violation
                        if vehicle_id in violated_vehicles:
                            continue
                            
                        helmet_violation = False
                        for px1, py1, px2, py2, pconf in persons:
                            # Check if person overlaps with motorcycle
                            if (px1 < mx2 and px2 > mx1 and py1 < my2 and py2 > my1):
                                # Simple helmet check - look for dark pixels in head region
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
                            violated_vehicles.add(vehicle_id)  # Mark this vehicle as violated
                            current_violations += 1
                            violations_found += 1
                            # Change vehicle border to RED for violation
                            cv2.rectangle(annotated_frame, (mx1, my1), (mx2, my2), (0, 0, 255), 4)
                            cv2.putText(annotated_frame, "🚨 NO HELMET VIOLATION", (mx1, my1-10), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
                            # Add to live violations list
                            live_violations.append({
                                'frame': frame_count,
                                'type': 'No Helmet Violation',
                                'vehicle': 'Motorcycle',
                                'confidence': f'{mconf:.1f}%',
                                'time': datetime.now().strftime('%H:%M:%S')
                            })

                            # Save to database
                            save_violation_to_db('No Helmet Violation', vehicle_id, location="Live Detection")
                    
                    # Check speeding violations (simplified for live detection)
                    if not hasattr(st.session_state, 'vehicle_positions'):
                        st.session_state.vehicle_positions = {}
                    
                    for vehicle_type, vehicle_list in vehicles.items():
                        for vx1, vy1, vx2, vy2, vconf in vehicle_list:
                            vehicle_center = ((vx1 + vx2) / 2, (vy1 + vy2) / 2)
                            vehicle_id = f"{vehicle_type[:-1]}_{int(vx1/50)}_{int(vy1/50)}"
                            
                            if vehicle_id in st.session_state.vehicle_positions:
                                prev_pos, prev_frame = st.session_state.vehicle_positions[vehicle_id]
                                distance_pixels = ((vehicle_center[0] - prev_pos[0])**2 + (vehicle_center[1] - prev_pos[1])**2)**0.5
                                frame_diff = frame_count - prev_frame
                                
                                if frame_diff > 0 and distance_pixels > 40 and vehicle_id not in violated_vehicles:
                                    estimated_speed = (distance_pixels / frame_diff) * 2
                                    if estimated_speed > 30:  # Speed threshold
                                        violated_vehicles.add(vehicle_id)
                                        current_violations += 1
                                        violations_found += 1
                                        # Change vehicle border to RED for violation
                                        cv2.rectangle(annotated_frame, (vx1, vy1), (vx2, vy2), (0, 0, 255), 4)
                                        cv2.putText(annotated_frame, "🚨 SPEEDING VIOLATION", (vx1, vy1-10), 
                                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                        
                                        live_violations.append({
                                            'frame': frame_count,
                                            'type': 'Speeding Violation',
                                            'vehicle': vehicle_type[:-1].title(),
                                            'confidence': f'{vconf:.1f}%',
                                            'time': datetime.now().strftime('%H:%M:%S')
                                        })

                                        # Save to database
                                        save_violation_to_db('Speeding Violation', vehicle_id, location="Live Detection")
                            
                            st.session_state.vehicle_positions[vehicle_id] = (vehicle_center, frame_count)
                    
                    # Check wrong way violations
                    for vehicle_type, vehicle_list in vehicles.items():
                        for vx1, vy1, vx2, vy2, vconf in vehicle_list:
                            vehicle_id = f"{vehicle_type[:-1]}_{int(vx1/50)}_{int(vy1/50)}"
                            current_pos = ((vx1 + vx2) / 2, (vy1 + vy2) / 2)
                            
                            if vehicle_id in st.session_state.vehicle_positions:
                                prev_pos, prev_frame = st.session_state.vehicle_positions[vehicle_id]
                                
                                # Check if moving upward (wrong way)
                                if current_pos[1] < prev_pos[1] - 25 and vehicle_id not in violated_vehicles:
                                    violated_vehicles.add(vehicle_id)
                                    current_violations += 1
                                    violations_found += 1
                                    # Change vehicle border to RED for violation
                                    cv2.rectangle(annotated_frame, (vx1, vy1), (vx2, vy2), (0, 0, 255), 4)
                                    cv2.putText(annotated_frame, "🚨 WRONG WAY VIOLATION", (vx1, vy1-10), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                    
                                    live_violations.append({
                                        'frame': frame_count,
                                        'type': 'Wrong Way Violation',
                                        'vehicle': vehicle_type[:-1].title(),
                                        'confidence': f'{vconf:.1f}%',
                                        'time': datetime.now().strftime('%H:%M:%S')
                                    })

                                    # Save to database
                                    save_violation_to_db('Wrong Way Violation', vehicle_id, location="Live Detection")
                    
                    # Check tailgating violations
                    all_vehicles = []
                    for vehicle_type, vehicle_list in vehicles.items():
                        for vx1, vy1, vx2, vy2, vconf in vehicle_list:
                            all_vehicles.append({
                                'bbox': (vx1, vy1, vx2, vy2),
                                'type': vehicle_type[:-1],
                                'conf': vconf
                            })
                    
                    for i, vehicle1 in enumerate(all_vehicles):
                        for j, vehicle2 in enumerate(all_vehicles[i+1:], i+1):
                            v1x1, v1y1, v1x2, v1y2 = vehicle1['bbox']
                            v2x1, v2y1, v2x2, v2y2 = vehicle2['bbox']
                            
                            center1 = ((v1x1 + v1x2) / 2, (v1y1 + v1y2) / 2)
                            center2 = ((v2x1 + v2x2) / 2, (v2y1 + v2y2) / 2)
                            distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
                            
                            if distance < 70 and abs(center1[0] - center2[0]) < 40:
                                vehicle_id = f"{vehicle1['type']}_{int(v1x1/50)}_{int(v1y1/50)}"
                                if vehicle_id not in violated_vehicles:
                                    violated_vehicles.add(vehicle_id)
                                    current_violations += 1
                                    violations_found += 1
                                    # Change vehicle border to RED for violation
                                    cv2.rectangle(annotated_frame, (v1x1, v1y1), (v1x2, v1y2), (0, 0, 255), 4)
                                    cv2.putText(annotated_frame, "🚨 TAILGATING VIOLATION", (v1x1, v1y1-10), 
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                    
                                    live_violations.append({
                                        'frame': frame_count,
                                        'type': 'Tailgating Violation',
                                        'vehicle': vehicle1['type'].title(),
                                        'confidence': f'{vehicle1["conf"]:.1f}%',
                                        'time': datetime.now().strftime('%H:%M:%S')
                                    })

                                    # Save to database
                                    save_violation_to_db('Tailgating Violation', vehicle_id, location="Live Detection")
                                    break
                    
                    # Check red light violations with improved detection
                    red_lights_detected = any(light[5] == 'red' for light in traffic_lights if len(light) > 5)
                    
                    if red_lights_detected:
                        for vehicle_type, vehicle_list in vehicles.items():
                            for vx1, vy1, vx2, vy2, vconf in vehicle_list:
                                vehicle_id = f"{vehicle_type}_{int(vx1/50)}_{int(vy1/50)}"
                                
                                if vehicle_id in violated_vehicles:
                                    continue
                                    
                                # Check if vehicle is in intersection area
                                if vy2 > frame.shape[0] * 0.7:
                                    violated_vehicles.add(vehicle_id)
                                    current_violations += 1
                                    violations_found += 1
                                    # Change vehicle border to RED for violation
                                    cv2.rectangle(annotated_frame, (vx1, vy1), (vx2, vy2), (0, 0, 255), 4)
                                    cv2.putText(annotated_frame, f"🚨 RED LIGHT VIOLATION", 
                                              (vx1, vy1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                                    
                                    live_violations.append({
                                        'frame': frame_count,
                                        'type': 'Red Light Violation',
                                        'vehicle': vehicle_type[:-1].title(),
                                        'confidence': f'{vconf:.1f}%',
                                        'time': datetime.now().strftime('%H:%M:%S')
                                    })

                                    # Save to database
                                    save_violation_to_db('Red Light Violation', vehicle_id, location="Live Detection")
                                    break
                    
                    # Add violation alert
                    if current_violations > 0:
                        cv2.rectangle(annotated_frame, (10, 10), (400, 50), (0, 0, 255), -1)
                        cv2.putText(annotated_frame, f"VIOLATIONS: {current_violations}", 
                                  (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                    
                    # Display frame
                    video_placeholder.image(annotated_frame, channels="BGR", use_container_width=True)
                    
                    # Update stats
                    with stats_placeholder.container():
                        # Main stats row
                        col1, col2, col3, col4, col5 = st.columns(5)
                        with col1:
                            st.metric("Frame", f"{frame_count}/{total_frames}")
                        with col2:
                            total_vehicles = sum(len(v) for v in vehicles.values())
                            st.metric("Total Vehicles", total_vehicles)
                        with col3:
                            st.metric("Traffic Lights", len(traffic_lights))
                        with col4:
                            st.metric("Total Violations", violations_found)
                        with col5:
                            st.metric("Current Violations", current_violations)
                        
                        # Vehicle breakdown
                        if total_vehicles > 0:
                            st.write("**Vehicle Breakdown:**")
                            vehicle_cols = st.columns(4)
                            with vehicle_cols[0]:
                                st.write(f"🚗 Cars: {len(vehicles['cars'])}")
                            with vehicle_cols[1]:
                                st.write(f"🏍️ Motorcycles: {len(vehicles['motorcycles'])}")
                            with vehicle_cols[2]:
                                st.write(f"🚌 Buses: {len(vehicles['buses'])}")
                            with vehicle_cols[3]:
                                st.write(f"🚛 Trucks: {len(vehicles['trucks'])}")
                    
                    # Update violations display
                    with violations_placeholder.container():
                        if live_violations:
                            st.write(f"**Total Violations: {len(live_violations)}**")
                            # Show last 5 violations
                            for violation in live_violations[-5:]:
                                with st.expander(f"{violation['type']} - Frame {violation['frame']}", expanded=False):
                                    st.write(f"**Vehicle:** {violation['vehicle']}")
                                    st.write(f"**Confidence:** {violation['confidence']}")
                                    st.write(f"**Time:** {violation['time']}")
                        else:
                            st.write("**No violations detected yet**")
                            st.info("Violations will appear here as they are detected in the video.")
                    
                    progress = frame_count / total_frames
                    progress_bar.progress(progress)
                    
                    frame_count += 1
                    
                    # Control playback speed (FPS)
                    time.sleep(1.0 / speed)
                    
                    # Check if stop was pressed
                    if st.session_state.get('stop_detection', False):
                        break
                
                cap.release()
                st.success(f"✅ Analysis complete! Found {violations_found} violations in {frame_count} frames.")
                
                # Show final violations summary
                if live_violations:
                    st.subheader("📋 Final Violations Summary")
                    violation_types = {}
                    for v in live_violations:
                        violation_types[v['type']] = violation_types.get(v['type'], 0) + 1
                    
                    for vtype, count in violation_types.items():
                        st.write(f"• {vtype}: {count} violations")
                st.session_state.start_detection = False
                st.session_state.stop_detection = False
        
        else:
            st.markdown("""
            <div class="success-card">
                <h3>📺 Live Detection Features</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                    <div>
                        <h4>🚨 Violation Detection:</h4>
                        <ul>
                            <li>Red Light Violations</li>
                            <li>No Helmet Violations</li>
                            <li>Speeding Detection</li>
                            <li>Wrong Way Driving</li>
                        </ul>
                    </div>
                    <div>
                        <h4>📊 Live Features:</h4>
                        <ul>
                            <li>Real-time Statistics</li>
                            <li>Playback Controls</li>
                            <li>Violation Alerts</li>
                            <li>Frame Analysis</li>
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    elif page == "🗄️ Archive History":
        st.markdown("## 🗄️ Archive Management")
        
        # Find all archive files
        archive_files = []
        for file in os.listdir('.'):
            if file.startswith('archive_violations_') or file == 'violations.db':
                archive_files.append(file)
        
        if not archive_files:
            st.info("No previous analysis found. All data is in current session.")
        else:
            st.write(f"Found {len(archive_files)} previous analysis sessions:")
            
            # Select archive to view
            selected_archive = st.selectbox("Choose Archive to View:", archive_files)
            
            if selected_archive:
                try:
                    # Load archive data
                    conn = sqlite3.connect(selected_archive)
                    archive_df = pd.read_sql_query("SELECT * FROM violations ORDER BY timestamp DESC", conn)
                    conn.close()
                    
                    if not archive_df.empty:
                        # Show archive stats
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Violations", len(archive_df))
                        with col2:
                            st.metric("Archive Date", selected_archive.replace('archive_violations_', '').replace('.db', ''))
                        with col3:
                            st.metric("Most Common Type", archive_df['violation_type'].mode().iloc[0] if not archive_df.empty else "None")
                        
                        # Show archive violations
                        st.subheader("Archive Violations")
                        st.dataframe(archive_df)
                        
                        # Show detailed view
                        st.subheader("Detailed Archive View")
                        for _, row in archive_df.head(5).iterrows():
                            with st.expander(f"{row['violation_type']} - {row['timestamp']}"):
                                col1, col2 = st.columns([1, 2])
                                
                                with col1:
                                    if os.path.exists(row['image_path']):
                                        image = Image.open(row['image_path'])
                                        st.image(image, caption="Archive Evidence")
                                    else:
                                        st.write("Image not found")
                                
                                with col2:
                                    st.write(f"**Type:** {row['violation_type']}")
                                    st.write(f"**Time:** {row['timestamp']}")
                                    st.write(f"**Vehicle ID:** {row['vehicle_id']}")
                                    if len(row) > 5:
                                        st.write(f"**Location:** {row.get('location', 'Unknown')}")
                                        st.write(f"**GPS:** {row.get('gps_coords', 'N/A')}")
                                        st.write(f"**Camera:** {row.get('camera_id', 'Unknown')}")
                    else:
                        st.info("This archive is empty.")
                        
                except Exception as e:
                    st.error(f"Error loading archive: {e}")
            
            # Archive management
            st.subheader("Archive Management")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Archive Current Session"):
                    if os.path.exists('current_session.db'):
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        shutil.copy('current_session.db', f'archive_violations_{timestamp}.db')
                        st.success(f"Current session archived as archive_violations_{timestamp}.db")
                        st.rerun()
            
            with col2:
                if st.button("Delete Selected Archive"):
                    if selected_archive and selected_archive != 'current_session.db':
                        os.remove(selected_archive)
                        st.success(f"Deleted {selected_archive}")
                        st.rerun()

if __name__ == "__main__":
    main()