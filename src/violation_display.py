"""
Enhanced violation display system with clear names and severity information
"""

import streamlit as st
from violation_categories import (
    get_violation_severity_info, 
    get_violation_display_name,
    get_violation_summary,
    VIOLATION_CATEGORIES
)

def display_violation_card(violation, show_details=True):
    """Display a single violation with enhanced information"""
    severity_info = get_violation_severity_info(violation['violation_type'])
    
    # Create violation card with severity-based styling
    severity_colors = {
        'CRITICAL': '#dc2626',  # Red
        'HIGH': '#ea580c',      # Orange  
        'MEDIUM': '#d97706',    # Amber
        'LOW': '#16a34a'        # Green
    }
    
    card_color = severity_colors.get(severity_info['category'], '#6b7280')
    
    st.markdown(f"""
    <div style="
        border-left: 5px solid {card_color};
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(51, 65, 85, 0.8) 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #f1f5f9;">
                    {severity_info['color']} {severity_info['emoji']} {severity_info['display_name']}
                </h4>
                <p style="margin: 0.25rem 0; color: #cbd5e1; font-size: 0.9rem;">
                    📅 {violation.get('timestamp', 'Unknown time')}
                </p>
                <p style="margin: 0; color: #94a3b8; font-size: 0.8rem;">
                    🚗 Vehicle: {violation.get('vehicle_id', 'Unknown')} | 📍 {violation.get('location', 'Unknown location')}
                </p>
            </div>
            <div style="text-align: right;">
                <span style="
                    background-color: {card_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: bold;
                ">
                    {severity_info['category']} PRIORITY
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if show_details:
        with st.expander("📋 Violation Details", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Show violation snapshot if available
                import os
                if violation.get('image_path') and os.path.exists(violation['image_path']):
                    from PIL import Image
                    try:
                        image = Image.open(violation['image_path'])
                        st.image(image, caption="📷 Violation Snapshot", use_container_width=True)
                    except:
                        st.info("📷 Snapshot not available")
                else:
                    st.info("📷 No snapshot available")
            
            with col2:
                st.markdown("**🚨 Severity Information**")
                st.write(f"**Priority Level:** {severity_info['category']}")
                st.write(f"**Description:** {severity_info['description']}")
                st.write(f"**Fine Range:** {severity_info['fine_range']}")
                st.write(f"**License Points:** {severity_info['points']}")
                
                st.markdown("**📍 Incident Details**")
                st.write(f"**Location:** {violation.get('location', 'Unknown')}")
                st.write(f"**GPS Coordinates:** {violation.get('gps_coords', 'N/A')}")
                st.write(f"**Camera ID:** {violation.get('camera_id', 'Unknown')}")
                st.write(f"**Consequences:** {severity_info['consequences']}")

def display_violations_summary(violations_df):
    """Display comprehensive violations summary"""
    if violations_df.empty:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #14532d 0%, #166534 100%);
            border: 1px solid #16a34a;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            color: #f0fdf4;
        ">
            <h3>✅ No Traffic Violations Detected</h3>
            <p>Excellent! All traffic rules are being followed properly.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    summary = get_violation_summary(violations_df)
    
    # Main summary header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #475569;
        text-align: center;
    ">
        <h2 style="color: #f1f5f9; margin: 0;">🚨 Traffic Violations Summary</h2>
        <h1 style="color: #ef4444; margin: 0.5rem 0;">{summary['total']} Total Violations</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Severity breakdown
    st.markdown("### 📊 Violation Severity Breakdown")
    
    cols = st.columns(len(summary['severity_breakdown']))
    for i, severity in enumerate(summary['severity_breakdown']):
        with cols[i]:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 12px;
                padding: 1rem;
                text-align: center;
                border: 1px solid #475569;
                margin: 0.5rem 0;
            ">
                <h3 style="color: #f1f5f9; margin: 0;">{severity['color']} {severity['category']}</h3>
                <h2 style="color: #ef4444; margin: 0.5rem 0;">{severity['count']}</h2>
                <p style="color: #cbd5e1; margin: 0; font-size: 0.8rem;">
                    {severity['percentage']:.1f}% of total
                </p>
                <p style="color: #94a3b8; margin: 0.5rem 0; font-size: 0.7rem;">
                    {severity['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Top violation types
    st.markdown("### 🔥 Most Common Violations")
    
    sorted_types = sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True)
    
    for i, (violation_type, count) in enumerate(sorted_types[:5]):
        percentage = (count / summary['total']) * 100
        
        # Get severity info for the violation type
        # Find original violation type from dataframe
        original_type = None
        for _, row in violations_df.iterrows():
            if get_violation_display_name(row['violation_type']) == violation_type:
                original_type = row['violation_type']
                break
        
        if original_type:
            severity_info = get_violation_severity_info(original_type)
            
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
                border-left: 4px solid {['#dc2626', '#ea580c', '#d97706', '#16a34a'][severity_info['priority']-1]};
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #f1f5f9;">
                            {severity_info['emoji']} {violation_type}
                        </h4>
                        <p style="margin: 0; color: #cbd5e1; font-size: 0.9rem;">
                            {severity_info['category']} Priority - {severity_info['description']}
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <h3 style="margin: 0; color: #ef4444;">{count}</h3>
                        <p style="margin: 0; color: #94a3b8; font-size: 0.8rem;">{percentage:.1f}%</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def display_violation_details_page(violations_df):
    """Display detailed violations page with enhanced information"""
    if violations_df.empty:
        st.info("No violations to display")
        return
    
    # Summary at top
    display_violations_summary(violations_df)
    
    st.markdown("---")
    st.markdown("### 📋 Detailed Violation Records")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Category filter
        categories = ['All'] + list(VIOLATION_CATEGORIES.keys())
        selected_category = st.selectbox("Filter by Priority:", categories)
    
    with col2:
        # Sort options
        sort_options = ['Newest First', 'Oldest First', 'Priority (High to Low)', 'Priority (Low to High)']
        sort_by = st.selectbox("Sort by:", sort_options)
    
    with col3:
        # Show count
        show_count = st.number_input("Show violations:", min_value=5, max_value=100, value=20, step=5)
    
    # Filter violations
    filtered_df = violations_df.copy()
    
    if selected_category != 'All':
        from violation_categories import get_violation_category
        filtered_df = filtered_df[filtered_df['violation_type'].apply(
            lambda x: get_violation_category(x) == selected_category
        )]
    
    # Sort violations
    if sort_by == 'Newest First':
        filtered_df = filtered_df.sort_values('timestamp', ascending=False)
    elif sort_by == 'Oldest First':
        filtered_df = filtered_df.sort_values('timestamp', ascending=True)
    elif sort_by == 'Priority (High to Low)':
        from violation_categories import get_violation_priority
        filtered_df['priority'] = filtered_df['violation_type'].apply(get_violation_priority)
        filtered_df = filtered_df.sort_values('priority', ascending=True)
    elif sort_by == 'Priority (Low to High)':
        from violation_categories import get_violation_priority
        filtered_df['priority'] = filtered_df['violation_type'].apply(get_violation_priority)
        filtered_df = filtered_df.sort_values('priority', ascending=False)
    
    # Display violations with snapshots
    st.write(f"Showing {min(len(filtered_df), show_count)} of {len(filtered_df)} violations")
    
    for _, violation in filtered_df.head(show_count).iterrows():
        severity_info = get_violation_severity_info(violation['violation_type'])
        
        with st.expander(f"{severity_info['emoji']} {severity_info['display_name']} - {violation['timestamp']}", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Show violation snapshot
                import os
                if violation.get('image_path') and os.path.exists(violation['image_path']):
                    from PIL import Image
                    try:
                        image = Image.open(violation['image_path'])
                        st.image(image, caption="📷 Violation Evidence", use_container_width=True)
                    except:
                        st.info("📷 Image not available")
                else:
                    st.info("📷 No snapshot captured")
            
            with col2:
                priority_colors = {'CRITICAL': 'red', 'HIGH': 'orange', 'MEDIUM': 'yellow', 'LOW': 'green'}
                st.markdown(f"**Priority:** :{priority_colors[severity_info['category']]}[{severity_info['category']}]")
                
                st.write(f"**Type:** {severity_info['display_name']}")
                st.write(f"**Time:** {violation['timestamp']}")
                st.write(f"**Vehicle ID:** {violation['vehicle_id']}")
                st.write(f"**Fine Range:** {severity_info['fine_range']}")
                st.write(f"**License Points:** {severity_info['points']}")
                st.write(f"**📍 Location:** {violation.get('location', 'Unknown')}")
                st.write(f"**🗺️ GPS:** {violation.get('gps_coords', 'N/A')}")
                st.write(f"**📹 Camera:** {violation.get('camera_id', 'Unknown')}")
                
                if violation.get('gps_coords') and violation.get('gps_coords') != '0.0, 0.0':
                    maps_url = f"https://maps.google.com/?q={violation['gps_coords']}"
                    st.markdown(f"[🗺️ View on Google Maps]({maps_url})")

def display_live_violation_alert(violation_type, vehicle_type, confidence, location="Live Detection"):
    """Display real-time violation alert"""
    severity_info = get_violation_severity_info(violation_type)
    
    # Alert styling based on severity
    alert_colors = {
        'CRITICAL': '#dc2626',
        'HIGH': '#ea580c', 
        'MEDIUM': '#d97706',
        'LOW': '#16a34a'
    }
    
    alert_color = alert_colors.get(severity_info['category'], '#6b7280')
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {alert_color}20 0%, {alert_color}10 100%);
        border: 2px solid {alert_color};
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        animation: pulse 2s infinite;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h4 style="margin: 0; color: #f1f5f9;">
                    🚨 {severity_info['emoji']} {severity_info['display_name']} DETECTED!
                </h4>
                <p style="margin: 0.25rem 0; color: #cbd5e1;">
                    Vehicle: {vehicle_type} | Confidence: {confidence} | Location: {location}
                </p>
            </div>
            <div style="
                background-color: {alert_color};
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 25px;
                font-weight: bold;
                font-size: 0.9rem;
            ">
                {severity_info['category']} PRIORITY
            </div>
        </div>
    </div>
    
    <style>
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 {alert_color}40; }}
        70% {{ box-shadow: 0 0 0 10px {alert_color}00; }}
        100% {{ box-shadow: 0 0 0 0 {alert_color}00; }}
    }}
    </style>
    """, unsafe_allow_html=True)
    
    return severity_info