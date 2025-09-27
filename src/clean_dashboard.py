import streamlit as st
import sqlite3
import pandas as pd
import cv2
import os
import shutil
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="Traffic Monitor", layout="wide")

# Force complete light theme
st.markdown("""
<style>
    /* Force light theme for entire app */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Sidebar light theme */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        color: #000000 !important;
    }
    
    /* All text elements */
    h1, h2, h3, h4, h5, h6, p, div, span, label {
        color: #000000 !important;
    }
    
    /* Metric styling */
    .stMetric {
        background: #ffffff !important;
        color: #000000 !important;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Button styling */
    .stButton > button {
        background: #007bff !important;
        color: white !important;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    
    /* Input fields */
    .stSelectbox > div > div, .stTextInput > div > div > input {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Override any dark theme */
    * {
        color: #000000 !important;
    }
    
    /* Specific overrides */
    [data-testid="metric-container"] {
        background-color: #ffffff !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

def load_violations():
    conn = sqlite3.connect('current_session.db')
    try:
        df = pd.read_sql_query("SELECT * FROM violations ORDER BY timestamp DESC", conn)
    except:
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
        df = pd.DataFrame()
    conn.close()
    return df

def main():
    st.markdown("""
    <div style="background: white; padding: 2rem; text-align: center; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #dee2e6;">
        <h1 style="color: #000000; margin-bottom: 0.5rem;">
            🚦 Traffic Violation Detection
        </h1>
        <p style="color: #666666; font-size: 1.1rem;">
            AI-powered traffic monitoring system
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #dee2e6;">
            <h3 style="color: #000000; margin: 0;">🎛️ Navigation</h3>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.selectbox("Select Page:", [
            "Dashboard", "Process Video", "Process Images", 
            "View Violations", "Live Detection", "Archive"
        ])
        
        st.divider()
        
        st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #dee2e6;">
            <h4 style="color: #000000; margin: 0;">⚙️ System Controls</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑️ Clear Data"):
            if os.path.exists('current_session.db'):
                os.remove('current_session.db')
            if os.path.exists('outputs/violations'):
                for file in os.listdir('outputs/violations'):
                    if file.endswith('.jpg'):
                        os.remove(f'outputs/violations/{file}')
            st.success("Data cleared!")
            st.rerun()
        
        st.divider()
        
        st.markdown("""
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border: 1px solid #dee2e6;">
            <h4 style="color: #000000; margin: 0;">📊 System Status</h4>
        </div>
        """, unsafe_allow_html=True)
        
        df = load_violations()
        st.metric("Total Records", len(df))
        st.markdown("""
        <div style="background: #d4edda; padding: 0.5rem; border-radius: 6px; border: 1px solid #c3e6cb;">
            <p style="color: #155724; margin: 0; font-weight: bold;">
                ✅ System Online
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if page == "Dashboard":
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; border: 1px solid #dee2e6;">
            <h2 style="color: #000000; margin: 0;">📊 Dashboard</h2>
        </div>
        """, unsafe_allow_html=True)
        df = load_violations()
        
        if not df.empty:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Violations", len(df))
            with col2:
                today = pd.Timestamp.now().strftime('%Y-%m-%d')
                today_count = len(df[df['timestamp'].str.contains(today)])
                st.metric("Today", today_count)
            with col3:
                most_common = df['violation_type'].mode().iloc[0] if not df.empty else "None"
                st.metric("Most Common", most_common.split('(')[0])
            with col4:
                locations = df['location'].nunique() if 'location' in df.columns else 1
                st.metric("Locations", locations)
            
            st.subheader("Recent Violations")
            for _, row in df.head(5).iterrows():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**🚨 {row['violation_type']}**")
                        st.write(f"📅 {row['timestamp'][:19]}")
                    with col2:
                        st.write(f"🚗 {row.get('vehicle_id', 'Unknown')}")
                        st.write(f"📍 {row.get('location', 'Unknown')}")
                    st.divider()
        else:
            st.info("No violations detected. Upload content to start monitoring.")
    
    elif page == "Process Video":
        st.header("🎥 Process Video")
        st.info("Upload a traffic video for violation detection")
        
        uploaded_file = st.file_uploader("Choose video", type=['mp4', 'avi', 'mov'])
        
        if uploaded_file:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.video(uploaded_file)
            with col2:
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Size:** {uploaded_file.size / 1024 / 1024:.1f} MB")
                
                if st.button("🚀 Analyze Video"):
                    with st.spinner("Processing..."):
                        with open(f"data/samples/{uploaded_file.name}", "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        from local_processor import LocalTrafficProcessor
                        processor = LocalTrafficProcessor()
                        processor.process_video(f"data/samples/{uploaded_file.name}")
                    
                    st.success("✅ Analysis complete!")
                    st.rerun()
    
    elif page == "Process Images":
        st.header("📷 Process Images")
        st.info("Upload traffic images for violation detection")
        
        uploaded_files = st.file_uploader(
            "Choose images", 
            type=['jpg', 'jpeg', 'png', 'bmp'], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} image(s) uploaded")
            
            cols = st.columns(min(len(uploaded_files), 4))
            for i, file in enumerate(uploaded_files[:4]):
                with cols[i]:
                    st.image(file, caption=file.name, use_container_width=True)
            
            if st.button("🔍 Analyze Images"):
                from image_processor import ImageViolationProcessor
                processor = ImageViolationProcessor()
                
                progress = st.progress(0)
                results = []
                
                for i, file in enumerate(uploaded_files):
                    input_path = f"data/samples/{file.name}"
                    with open(input_path, "wb") as f:
                        f.write(file.getbuffer())
                    
                    output_path = f"outputs/violations/analyzed_{file.name}"
                    annotated_image, violations = processor.process_image(input_path, output_path)
                    
                    results.append({
                        'filename': file.name,
                        'violations': violations,
                        'annotated_image': annotated_image
                    })
                    
                    progress.progress((i + 1) / len(uploaded_files))
                
                st.success(f"✅ Processed {len(uploaded_files)} images!")
                
                total_violations = sum(len(r['violations']) for r in results)
                st.metric("Total Violations Found", total_violations)
                
                for result in results:
                    with st.expander(f"📷 {result['filename']} - {len(result['violations'])} violations"):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            if result['annotated_image'] is not None:
                                st.image(result['annotated_image'], channels="BGR", use_container_width=True)
                        with col2:
                            if result['violations']:
                                for i, v in enumerate(result['violations'], 1):
                                    st.write(f"**{i}. {v['type'].replace('_', ' ').title()}**")
                                    st.write(f"Vehicle: {v['vehicle_type'].title()}")
                                    st.write(f"Confidence: {v['confidence']:.1%}")
                            else:
                                st.info("No violations detected")
    
    elif page == "View Violations":
        st.header("🚨 View Violations")
        df = load_violations()
        
        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"{row['violation_type']} - {row['timestamp']}"):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if os.path.exists(row['image_path']):
                            image = Image.open(row['image_path'])
                            st.image(image, caption="Evidence")
                    with col2:
                        st.write(f"**Type:** {row['violation_type']}")
                        st.write(f"**Time:** {row['timestamp']}")
                        st.write(f"**Vehicle:** {row['vehicle_id']}")
                        st.write(f"**Location:** {row.get('location', 'Unknown')}")
        else:
            st.info("No violations recorded yet.")
    
    elif page == "Live Detection":
        st.header("📺 Live Detection")
        st.info("Upload a video for real-time analysis")
        
        uploaded_file = st.file_uploader("Choose video", type=['mp4', 'avi', 'mov'])
        
        if uploaded_file:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("▶️ Start"):
                    st.session_state.start_detection = True
            with col2:
                if st.button("⏹️ Stop"):
                    st.session_state.start_detection = False
            with col3:
                speed = st.slider("Speed (FPS)", 1, 30, 10)
            with col4:
                max_frames = st.number_input("Max Frames", 0, 1000, 0)
            
            if st.session_state.get('start_detection', False):
                st.info("Live detection would run here...")
        else:
            st.info("📹 Upload a video to start live detection")
    
    elif page == "Archive":
        st.header("🗄️ Archive History")
        
        archive_files = [f for f in os.listdir('.') if f.startswith('archive_violations_')]
        
        if archive_files:
            selected = st.selectbox("Choose Archive:", archive_files)
            
            if selected:
                conn = sqlite3.connect(selected)
                archive_df = pd.read_sql_query("SELECT * FROM violations", conn)
                conn.close()
                
                if not archive_df.empty:
                    st.metric("Archive Violations", len(archive_df))
                    st.dataframe(archive_df)
        else:
            st.info("No archives found.")

if __name__ == "__main__":
    main()