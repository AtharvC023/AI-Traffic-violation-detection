import sqlite3
import shutil
import os
from datetime import datetime

def clear_current_session():
    """Clear current session data"""
    if os.path.exists('current_session.db'):
        os.remove('current_session.db')
    
    # Clear violation images
    if os.path.exists('outputs/violations'):
        for file in os.listdir('outputs/violations'):
            os.remove(f'outputs/violations/{file}')
    
    print("✅ Current session cleared!")

def archive_old_data():
    """Move old violations to archive"""
    if os.path.exists('violations.db'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        shutil.move('violations.db', f'archive_violations_{timestamp}.db')
        print(f"✅ Old data archived as archive_violations_{timestamp}.db")

def view_archived_data():
    """View old archived violations"""
    archive_files = [f for f in os.listdir('.') if f.startswith('archive_violations_')]
    
    if not archive_files:
        print("No archived data found")
        return
    
    print("📁 Archived Sessions:")
    for i, file in enumerate(archive_files):
        conn = sqlite3.connect(file)
        cursor = conn.execute("SELECT COUNT(*) FROM violations")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"{i+1}. {file} - {count} violations")

if __name__ == "__main__":
    print("Archive Manager")
    print("1. Clear current session")
    print("2. Archive old data") 
    print("3. View archived data")
    
    choice = input("Choose option (1-3): ")
    
    if choice == "1":
        clear_current_session()
    elif choice == "2":
        archive_old_data()
    elif choice == "3":
        view_archived_data()