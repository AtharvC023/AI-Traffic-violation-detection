#!/usr/bin/env python3
"""
Violation Analysis Tool - Analyze detected traffic violations
"""

import sqlite3
import pandas as pd
from datetime import datetime

def analyze_violations():
    print("Traffic Violation Analysis")
    print("=" * 40)
    
    # Connect to database
    df = pd.DataFrame()
    
    # Try current session first
    try:
        conn = sqlite3.connect('current_session.db')
        df = pd.read_sql_query("SELECT * FROM violations ORDER BY timestamp DESC", conn)
        conn.close()
        print("Analyzing current session violations...")
    except:
        pass
    
    # If no current session, try main violations.db
    if df.empty:
        try:
            conn = sqlite3.connect('violations.db')
            df = pd.read_sql_query("SELECT * FROM violations ORDER BY timestamp DESC", conn)
            conn.close()
            print("Analyzing historical violations...")
        except:
            print("No violations database found. Run detection first.")
            return
    
    if df.empty:
        print("No violations detected yet.")
        return
    
    print(f"Total Violations Found: {len(df)}")
    print()
    
    # Violation Type Analysis
    print("VIOLATION TYPE BREAKDOWN:")
    violation_counts = df['violation_type'].value_counts()
    for violation, count in violation_counts.items():
        percentage = (count / len(df)) * 100
        print(f"  • {violation}: {count} ({percentage:.1f}%)")
    
    
    print()
    
    # Vehicle Type Analysis
    print("VEHICLE TYPE ANALYSIS:")
    vehicle_types = df['vehicle_id'].str.extract(r'(\w+)_\d+')[0].value_counts()
    for vehicle, count in vehicle_types.items():
        percentage = (count / len(df)) * 100
        print(f"  • {vehicle}: {count} violations ({percentage:.1f}%)")
    
    print()
    
    # Check if location column exists
    if 'location' in df.columns:
        print("LOCATION HOTSPOTS:")
        location_counts = df['location'].value_counts()
        for location, count in location_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  • {location}: {count} violations ({percentage:.1f}%)")
        print()
    else:
        print("LOCATION ANALYSIS: Not available in this dataset")
        print()
    
    # Time Analysis
    print("TIME PATTERN ANALYSIS:")
    try:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        hourly_counts = df['hour'].value_counts().sort_index()
        
        if not hourly_counts.empty:
            peak_hour = hourly_counts.idxmax()
            peak_count = hourly_counts.max()
            print(f"  • Peak violation hour: {peak_hour}:00 ({peak_count} violations)")
            print(f"  • Most active period: {dict(list(hourly_counts.head(3).items()))}")
        else:
            print(f"  • No time pattern data available")
    except:
        print(f"  • Time analysis not available for this dataset")
    
    print()
    
    # Recent Violations Detail
    print("RECENT VIOLATIONS (Last 5):")
    for idx, row in df.head(5).iterrows():
        print(f"  {idx+1}. {row['violation_type']}")
        print(f"     Time: {row['timestamp']}")
        if 'location' in df.columns:
            print(f"     Location: {row['location']}")
        print(f"     Vehicle: {row['vehicle_id']}")
        if 'image_path' in df.columns:
            print(f"     Evidence: {row['image_path']}")
        print()
    
    # Summary Statistics
    print("SUMMARY STATISTICS:")
    print(f"  • First violation: {df['timestamp'].min()}")
    print(f"  • Last violation: {df['timestamp'].max()}")
    print(f"  • Most common violation: {violation_counts.index[0]}")
    print(f"  • Most problematic vehicle type: {vehicle_types.index[0] if not vehicle_types.empty else 'N/A'}")
    if 'location' in df.columns:
        location_counts = df['location'].value_counts()
        print(f"  • Hotspot location: {location_counts.index[0]}")
    print(f"  • Total evidence files: {len(df[df['image_path'].notna()]) if 'image_path' in df.columns else 'N/A'}")

if __name__ == "__main__":
    analyze_violations()