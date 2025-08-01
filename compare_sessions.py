#!/usr/bin/env python3
"""
FocusON Session Comparison Tool
Compares multiple sessions from the reports folder
"""

import json
import os
from datetime import datetime

def compare_sessions():
    """Compare all sessions in the reports folder"""
    reports_dir = "reports"
    
    if not os.path.exists(reports_dir):
        print("No reports folder found. Run FocusON first to generate sessions.")
        return
    
    # Find all session folders
    session_folders = [f for f in os.listdir(reports_dir) if f.startswith("session_")]
    
    if len(session_folders) < 2:
        print(f"Found {len(session_folders)} session(s). Need at least 2 sessions to compare.")
        return
    
    sessions = []
    
    for folder in session_folders:
        data_file = os.path.join(reports_dir, folder, "session_data.json")
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    sessions.append({
                        'folder': folder,
                        'data': data,
                        'start_time': data.get('start_time', 0)
                    })
            except Exception as e:
                print(f"Error loading {data_file}: {e}")
    
    if len(sessions) < 2:
        print("Need at least 2 valid session files to compare.")
        return
    
    # Sort by start time
    sessions.sort(key=lambda x: x['start_time'])
    
    # Generate comparison report
    print("\n" + "="*80)
    print("                           FOCUSON SESSION COMPARISON")
    print("="*80)
    
    for i, session in enumerate(sessions, 1):
        data = session['data']
        session_date = datetime.fromtimestamp(data['start_time']).strftime("%Y-%m-%d %H:%M")
        
        print(f"\n📊 SESSION {i} - {session_date}:")
        print(f"   • Duration: {data.get('duration', 0)/60:.1f} minutes")
        print(f"   • Focus Score: {data.get('avg_focus_score', 0):.1f}/100")
        print(f"   • Productivity: {data.get('productivity_percentage', 0):.1f}%")
        print(f"   • Total Blinks: {data.get('blink_count', 0)}")
        print(f"   • Distractions: {data.get('distraction_count', 0)}")
    
    # Calculate improvements
    if len(sessions) >= 2:
        first = sessions[0]['data']
        last = sessions[-1]['data']
        
        focus_change = last.get('avg_focus_score', 0) - first.get('avg_focus_score', 0)
        productivity_change = last.get('productivity_percentage', 0) - first.get('productivity_percentage', 0)
        
        print(f"\n📈 IMPROVEMENT ANALYSIS:")
        print(f"   • Focus Score Change: {focus_change:+.1f} points")
        print(f"   • Productivity Change: {productivity_change:+.1f}%")
        
        if focus_change > 0:
            print("   • 🎉 Focus has improved over time!")
        elif focus_change < 0:
            print("   • 📉 Focus has declined - consider reviewing your routine")
        else:
            print("   • ➡️  Focus has remained stable")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    compare_sessions() 