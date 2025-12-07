"""
Traffic violation analysis report generator
"""

import pandas as pd
import sqlite3
from datetime import datetime
import json
import os
from violation_categories import get_violation_severity_info, get_violation_summary, VIOLATION_CATEGORIES

class ViolationReportGenerator:
    def __init__(self):
        self.db_path = 'current_session.db'
    
    def generate_report(self, format='json'):
        """Generate comprehensive violation report"""
        df = self.load_violations()
        
        if df.empty:
            return self._empty_report()
        
        report_data = {
            'analysis_info': self._get_analysis_info(df),
            'summary': self._get_summary_stats(df),
            'violations_by_priority': self._get_priority_breakdown(df),
            'violations_by_type': self._get_type_breakdown(df),
            'detailed_violations': self._get_detailed_violations(df),
            'recommendations': self._get_recommendations(df)
        }
        
        if format == 'json':
            return self._save_json_report(report_data)
        elif format == 'csv':
            return self._save_csv_report(df, report_data)
        elif format == 'txt':
            return self._save_text_report(report_data)
    
    def load_violations(self):
        """Load violations from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT * FROM violations ORDER BY timestamp DESC", conn)
            conn.close()
            return df
        except:
            return pd.DataFrame()
    
    def _get_analysis_info(self, df):
        """Get analysis metadata"""
        return {
            'report_generated': datetime.now().isoformat(),
            'total_violations': len(df),
            'analysis_period': {
                'start': df['timestamp'].min() if not df.empty else None,
                'end': df['timestamp'].max() if not df.empty else None
            },
            'unique_vehicles': df['vehicle_id'].nunique() if not df.empty else 0,
            'locations_analyzed': df['location'].nunique() if not df.empty else 0
        }
    
    def _get_summary_stats(self, df):
        """Get summary statistics"""
        summary = get_violation_summary(df)
        return {
            'total_violations': summary['total'],
            'by_category': summary['by_category'],
            'most_common_violation': max(summary['by_type'].items(), key=lambda x: x[1])[0] if summary['by_type'] else None,
            'severity_distribution': summary['severity_breakdown']
        }
    
    def _get_priority_breakdown(self, df):
        """Get violations grouped by priority"""
        breakdown = {}
        for _, violation in df.iterrows():
            info = get_violation_severity_info(violation['violation_type'])
            category = info['category']
            if category not in breakdown:
                breakdown[category] = []
            breakdown[category].append({
                'type': info['display_name'],
                'timestamp': violation['timestamp'],
                'vehicle_id': violation['vehicle_id'],
                'location': violation.get('location', 'Unknown')
            })
        return breakdown
    
    def _get_type_breakdown(self, df):
        """Get violations grouped by type"""
        breakdown = {}
        for _, violation in df.iterrows():
            info = get_violation_severity_info(violation['violation_type'])
            vtype = info['display_name']
            if vtype not in breakdown:
                breakdown[vtype] = {
                    'count': 0,
                    'priority': info['category'],
                    'fine_range': info['fine_range'],
                    'violations': []
                }
            breakdown[vtype]['count'] += 1
            breakdown[vtype]['violations'].append({
                'timestamp': violation['timestamp'],
                'vehicle_id': violation['vehicle_id'],
                'location': violation.get('location', 'Unknown')
            })
        return breakdown
    
    def _get_detailed_violations(self, df):
        """Get detailed violation list"""
        violations = []
        for _, violation in df.iterrows():
            info = get_violation_severity_info(violation['violation_type'])
            violations.append({
                'violation_name': info['display_name'],
                'priority': info['category'],
                'timestamp': violation['timestamp'],
                'vehicle_id': violation['vehicle_id'],
                'location': violation.get('location', 'Unknown'),
                'camera_id': violation.get('camera_id', 'Unknown'),
                'gps_coords': violation.get('gps_coords', 'N/A'),
                'fine_range': info['fine_range'],
                'license_points': info['points'],
                'consequences': info['consequences']
            })
        return violations
    
    def _get_recommendations(self, df):
        """Generate recommendations based on violations"""
        summary = get_violation_summary(df)
        recommendations = []
        
        # Priority-based recommendations
        for category_info in summary['severity_breakdown']:
            category = category_info['category']
            count = category_info['count']
            
            if category == 'CRITICAL' and count > 0:
                recommendations.append({
                    'priority': 'URGENT',
                    'issue': f"{count} critical violations detected",
                    'action': "Immediate enforcement required. Review traffic light timing and intersection safety."
                })
            elif category == 'HIGH' and count > 2:
                recommendations.append({
                    'priority': 'HIGH',
                    'issue': f"{count} high-priority safety violations",
                    'action': "Increase safety awareness campaigns and enforcement patrols."
                })
        
        # Type-specific recommendations
        if summary['by_type'].get('Red Light Running', 0) > 1:
            recommendations.append({
                'priority': 'HIGH',
                'issue': "Multiple red light violations",
                'action': "Install red light cameras and extend yellow light duration."
            })
        
        if summary['by_type'].get('No Helmet Usage', 0) > 1:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': "Helmet compliance issues",
                'action': "Increase helmet safety education and enforcement for motorcyclists."
            })
        
        return recommendations
    
    def _empty_report(self):
        """Generate report for no violations"""
        return {
            'status': 'success',
            'message': 'No violations detected',
            'file_path': None,
            'data': {
                'analysis_info': {
                    'report_generated': datetime.now().isoformat(),
                    'total_violations': 0
                },
                'summary': 'No traffic violations were detected in the analysis.'
            }
        }
    
    def _save_json_report(self, data):
        """Save report as JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'traffic_violation_report_{timestamp}.json'
        filepath = os.path.join('outputs', filename)
        
        os.makedirs('outputs', exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return {
            'status': 'success',
            'message': f'JSON report generated successfully',
            'file_path': filepath,
            'data': data
        }
    
    def _save_csv_report(self, df, report_data):
        """Save report as CSV"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'traffic_violations_{timestamp}.csv'
        filepath = os.path.join('outputs', filename)
        
        os.makedirs('outputs', exist_ok=True)
        
        # Create enhanced CSV with violation details
        enhanced_df = df.copy()
        enhanced_df['violation_display_name'] = enhanced_df['violation_type'].apply(
            lambda x: get_violation_severity_info(x)['display_name']
        )
        enhanced_df['priority'] = enhanced_df['violation_type'].apply(
            lambda x: get_violation_severity_info(x)['category']
        )
        enhanced_df['fine_range'] = enhanced_df['violation_type'].apply(
            lambda x: get_violation_severity_info(x)['fine_range']
        )
        
        enhanced_df.to_csv(filepath, index=False)
        
        return {
            'status': 'success',
            'message': f'CSV report generated successfully',
            'file_path': filepath,
            'data': report_data
        }
    
    def _save_text_report(self, data):
        """Save report as text file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'traffic_violation_report_{timestamp}.txt'
        filepath = os.path.join('outputs', filename)
        
        os.makedirs('outputs', exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write("TRAFFIC VIOLATION ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Analysis info
            f.write("ANALYSIS INFORMATION\n")
            f.write("-" * 20 + "\n")
            f.write(f"Report Generated: {data['analysis_info']['report_generated']}\n")
            f.write(f"Total Violations: {data['analysis_info']['total_violations']}\n")
            f.write(f"Unique Vehicles: {data['analysis_info']['unique_vehicles']}\n\n")
            
            # Summary
            f.write("VIOLATION SUMMARY\n")
            f.write("-" * 17 + "\n")
            for category, info in data['summary']['by_category'].items():
                f.write(f"{category}: {info['count']} violations ({info['percentage']:.1f}%)\n")
            f.write(f"\nMost Common: {data['summary']['most_common_violation']}\n\n")
            
            # Detailed violations
            f.write("DETAILED VIOLATIONS\n")
            f.write("-" * 19 + "\n")
            for violation in data['detailed_violations']:
                f.write(f"• {violation['violation_name']} ({violation['priority']})\n")
                f.write(f"  Time: {violation['timestamp']}\n")
                f.write(f"  Vehicle: {violation['vehicle_id']}\n")
                f.write(f"  Location: {violation['location']}\n")
                f.write(f"  Fine: {violation['fine_range']}\n\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 15 + "\n")
            for rec in data['recommendations']:
                f.write(f"• {rec['issue']} ({rec['priority']})\n")
                f.write(f"  Action: {rec['action']}\n\n")
        
        return {
            'status': 'success',
            'message': f'Text report generated successfully',
            'file_path': filepath,
            'data': data
        }