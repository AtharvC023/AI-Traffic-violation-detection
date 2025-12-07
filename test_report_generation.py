#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for report generation functionality
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add src to path
sys.path.append('src')

def create_sample_violations():
    """Create sample violations for testing"""
    conn = sqlite3.connect('current_session.db')
    
    # Create table
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
    
    # Clear existing data
    conn.execute('DELETE FROM violations')
    
    # Sample violations
    sample_violations = [
        ('red_light_violation', 'car_001', 'Main St & 5th Ave'),
        ('no_helmet_violation', 'bike_002', 'Highway 101'),
        ('speeding_violation', 'car_003', 'Downtown Area'),
        ('wrong_way_violation', 'bike_004', 'One Way Street'),
        ('tailgating_violation', 'car_005', 'Highway 101'),
        ('red_light_violation', 'car_006', 'Main St & 5th Ave'),
        ('no_helmet_violation', 'bike_007', 'City Center'),
    ]
    
    for i, (vtype, vehicle, location) in enumerate(sample_violations):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('''
            INSERT INTO violations (timestamp, violation_type, image_path, vehicle_id, location, gps_coords, camera_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, vtype, f'outputs/violations/sample_{i}.jpg', vehicle, location, '40.7128, -74.0060', f'CAM_{i+1:03d}'))
    
    conn.commit()
    conn.close()
    print(f"Created {len(sample_violations)} sample violations")

def test_report_generation():
    """Test all report formats"""
    from report_generator import ViolationReportGenerator
    
    generator = ViolationReportGenerator()
    
    print("\nTesting Report Generation...")
    print("=" * 40)
    
    # Test JSON report
    print("\n1. Generating JSON Report...")
    result = generator.generate_report('json')
    if result['status'] == 'success':
        print(f"SUCCESS JSON Report: {result['file_path']}")
        print(f"   Total violations: {result['data']['analysis_info']['total_violations']}")
    else:
        print(f"FAILED JSON Report: {result.get('message', 'Unknown error')}")
    
    # Test CSV report
    print("\n2. Generating CSV Report...")
    result = generator.generate_report('csv')
    if result['status'] == 'success':
        print(f"SUCCESS CSV Report: {result['file_path']}")
    else:
        print(f"FAILED CSV Report: {result.get('message', 'Unknown error')}")
    
    # Test Text report
    print("\n3. Generating Text Report...")
    result = generator.generate_report('txt')
    if result['status'] == 'success':
        print(f"SUCCESS Text Report: {result['file_path']}")
    else:
        print(f"FAILED Text Report: {result.get('message', 'Unknown error')}")
    
    print("\n" + "=" * 40)
    print("Report generation test completed!")
    print("Check the 'outputs' folder for generated reports.")

if __name__ == "__main__":
    print("Traffic Violation Report Generation Test")
    print("=" * 50)
    
    # Create sample data
    create_sample_violations()
    
    # Test report generation
    test_report_generation()