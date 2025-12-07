#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script to show enhanced violation categorization system
"""

import sys
import os
sys.path.append('src')

from violation_categories import (
    get_violation_severity_info,
    get_violation_display_name,
    get_violation_summary,
    VIOLATION_CATEGORIES
)

def demo_violation_info():
    """Demonstrate the enhanced violation information system"""
    
    print("Enhanced Traffic Violation System Demo")
    print("=" * 60)
    
    # Sample violation types from the system
    sample_violations = [
        'red_light_violation',
        'no_helmet_violation', 
        'speeding_violation',
        'wrong_way_violation',
        'tailgating_violation',
        'illegal_parking_violation'
    ]
    
    print("\nVIOLATION SEVERITY BREAKDOWN")
    print("-" * 60)
    
    for violation_type in sample_violations:
        info = get_violation_severity_info(violation_type)
        
        print(f"\n{info['display_name']}")
        print(f"   Priority: {info['category']}")
        print(f"   Description: {info['description']}")
        print(f"   Fine Range: {info['fine_range']}")
        print(f"   License Points: {info['points']}")
        print(f"   Consequences: {info['consequences']}")
    
    print("\n\nPRIORITY CATEGORIES")
    print("-" * 60)
    
    for category, data in VIOLATION_CATEGORIES.items():
        print(f"\n{category} PRIORITY")
        print(f"   Description: {data['description']}")
        print(f"   Priority Level: {data['priority']}")
        print(f"   Violations:")
        for violation in data['violations'][:3]:  # Show first 3
            display_name = get_violation_display_name(violation)
            print(f"     - {display_name}")
    
    print("\n\nSYSTEM FEATURES")
    print("-" * 60)
    print("- Clear violation names (e.g., 'Red Light Running' instead of 'red_light_violation')")
    print("- Priority-based categorization (CRITICAL, HIGH, MEDIUM, LOW)")
    print("- Detailed severity information including fines and consequences")
    print("- Visual indicators with emojis and color coding")
    print("- Comprehensive violation summaries and analytics")
    print("- Real-time violation alerts with severity-based styling")
    
    print("\n\nHOW USERS BENEFIT")
    print("-" * 60)
    print("+ Immediately understand violation severity")
    print("+ Know potential fines and consequences")
    print("+ See clear, user-friendly violation names")
    print("+ Prioritize which violations need immediate attention")
    print("+ Get comprehensive violation analytics")
    print("+ Receive real-time alerts with appropriate urgency")

if __name__ == "__main__":
    demo_violation_info()