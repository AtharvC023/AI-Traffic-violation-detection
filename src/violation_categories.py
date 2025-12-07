"""
Violation categorization and management system
"""

VIOLATION_CATEGORIES = {
    'CRITICAL': {
        'color': '🔴',
        'priority': 1,
        'description': 'Life-threatening violations requiring immediate action',
        'violations': [
            'Red Light Violation',
            'red_light_violation',
            'Stop Sign Violation',
            'Emergency Lane Violation',
            'crosswalk_violation'
        ]
    },
    'HIGH': {
        'color': '🟠', 
        'priority': 2,
        'description': 'Serious safety violations with high accident risk',
        'violations': [
            'No Helmet Violation',
            'no_helmet_violation',
            'Reckless Driving',
            'tailgating_violation'
        ]
    },
    'MEDIUM': {
        'color': '🟡',
        'priority': 3,
        'description': 'Traffic rule violations that may cause accidents',
        'violations': [
            'Speeding Violation',
            'speeding_violation',
            'Wrong Way Violation',
            'wrong_way_violation',
            'Lane Change Violation',
            'lane_violation'
        ]
    },
    'LOW': {
        'color': '🟢',
        'priority': 4,
        'description': 'Minor violations that disrupt traffic flow',
        'violations': [
            'Phone Use Violation',
            'Seatbelt Violation',
            'Parking Violation',
            'illegal_parking_violation'
        ]
    }
}

VIOLATION_EMOJIS = {
    'Red Light Violation': '🚦',
    'red_light_violation': '🚦',
    'Stop Sign Violation': '🛑',
    'No Helmet Violation': '🏍️',
    'no_helmet_violation': '🏍️',

    'Speeding Violation': '🏃',
    'speeding_violation': '🏃',
    'Wrong Way Violation': '↩️',
    'wrong_way_violation': '↩️',
    'Lane Change Violation': '🚗',
    'lane_violation': '🚗',
    'Phone Use Violation': '📱',
    'Seatbelt Violation': '🔒',
    'Parking Violation': '🅿️',
    'illegal_parking_violation': '🅿️',
    'tailgating_violation': '🚗',
    'crosswalk_violation': '🚶'
}

def get_violation_category(violation_type):
    """Get category for a violation type"""
    # Clean the violation type (remove parentheses and extra info)
    clean_type = violation_type.split('(')[0].strip()
    
    for category, data in VIOLATION_CATEGORIES.items():
        if clean_type in data['violations'] or violation_type in data['violations']:
            return category
    return 'MEDIUM'  # Default category

def get_violation_priority(violation_type):
    """Get priority level for a violation type"""
    category = get_violation_category(violation_type)
    return VIOLATION_CATEGORIES[category]['priority']

def get_violation_emoji(violation_type):
    """Get emoji for a violation type"""
    return VIOLATION_EMOJIS.get(violation_type, '⚠️')

def get_violation_display_name(violation_type):
    """Convert violation type to user-friendly display name"""
    display_names = {
        'red_light_violation': 'Red Light Running',
        'no_helmet_violation': 'No Helmet Usage',
        'speeding_violation': 'Speed Limit Exceeded',
        'wrong_way_violation': 'Wrong Way Driving',
        'lane_violation': 'Lane Violation',
        'illegal_parking_violation': 'Illegal Parking',
        'tailgating_violation': 'Following Too Close',
        'crosswalk_violation': 'Pedestrian Crosswalk Violation'
    }
    return display_names.get(violation_type, violation_type.replace('_', ' ').title())

def get_violation_severity_info(violation_type):
    """Get detailed severity information for a violation"""
    category = get_violation_category(violation_type)
    category_info = VIOLATION_CATEGORIES[category]
    
    severity_details = {
        'CRITICAL': {
            'fine_range': '$500 - $2000',
            'points': '6-12 points',
            'consequences': 'License suspension possible, Court appearance required'
        },
        'HIGH': {
            'fine_range': '$200 - $800',
            'points': '3-6 points',
            'consequences': 'Mandatory safety course, Insurance premium increase'
        },
        'MEDIUM': {
            'fine_range': '$100 - $400',
            'points': '2-4 points',
            'consequences': 'Traffic school option, Insurance notification'
        },
        'LOW': {
            'fine_range': '$50 - $200',
            'points': '1-2 points',
            'consequences': 'Warning possible, Minor insurance impact'
        }
    }
    
    return {
        'category': category,
        'priority': category_info['priority'],
        'description': category_info['description'],
        'color': category_info['color'],
        'emoji': get_violation_emoji(violation_type),
        'display_name': get_violation_display_name(violation_type),
        **severity_details[category]
    }

def categorize_violations(violations_df):
    """Categorize violations from dataframe"""
    if violations_df.empty:
        return {}
    
    categorized = {}
    for category in VIOLATION_CATEGORIES.keys():
        categorized[category] = []
    
    for _, violation in violations_df.iterrows():
        category = get_violation_category(violation['violation_type'])
        categorized[category].append(violation)
    
    return categorized

def get_violation_summary(violations_df):
    """Get comprehensive violation summary with severity breakdown"""
    if violations_df.empty:
        return {'total': 0, 'by_category': {}, 'by_type': {}}
    
    categorized = categorize_violations(violations_df)
    
    summary = {
        'total': len(violations_df),
        'by_category': {},
        'by_type': {},
        'severity_breakdown': []
    }
    
    for category, violations in categorized.items():
        summary['by_category'][category] = {
            'count': len(violations),
            'percentage': (len(violations) / len(violations_df)) * 100,
            'description': VIOLATION_CATEGORIES[category]['description']
        }
    
    # Count by violation type
    for _, violation in violations_df.iterrows():
        vtype = violation['violation_type']
        display_name = get_violation_display_name(vtype)
        if display_name not in summary['by_type']:
            summary['by_type'][display_name] = 0
        summary['by_type'][display_name] += 1
    
    # Create severity breakdown for display
    for category, data in VIOLATION_CATEGORIES.items():
        count = len(categorized[category])
        if count > 0:
            summary['severity_breakdown'].append({
                'category': category,
                'count': count,
                'color': data['color'],
                'description': data['description'],
                'percentage': (count / len(violations_df)) * 100
            })
    
    return summary