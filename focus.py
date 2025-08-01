import cv2
import time
import os
import base64
import json
import serial
from datetime import datetime
from openai import OpenAI
from PIL import ImageGrab, Image
from gaze_tracking import GazeTracking

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)

# Session tracking variables
session_start_time = time.time()
session_data = {
    'start_time': session_start_time,
    'blink_count': 0,
    'productive_time': 0,
    'distraction_count': 0,
    'focus_score_total': 0,
    'data_points': 0
}

# Persistent focus score tracking
focus_score = 100  # Start with perfect score
focus_score_decay_rate = 0.1  # Score recovers slowly over time
last_score_update = time.time()

# Distraction event tracking (to prevent repeated penalties)
blink_penalty_applied = False
eye_contact_penalty_applied = False
productivity_penalty_applied = False

# Blink tracking variables
blink_count = 0
last_blink_time = time.time()
blink_start_time = time.time()
is_blinking_state = False  # To track blink state changes

# Baseline tracking variables
baseline_bpm = None
baseline_established = False
baseline_start_time = time.time()
baseline_duration = 30  # 30 seconds to establish baseline
change_message = ""
change_message_time = 0
change_message_duration = 3  # Show message for 3 seconds

# Eye contact tracking variables
eye_contact_start_time = time.time()
looking_away_start_time = None
eye_contact_threshold = 5  # 5 seconds threshold
eye_contact_message = ""
eye_contact_message_time = 0
eye_contact_message_duration = 3  # Show message for 3 seconds

# Screenshot and productivity tracking variables
screenshot_interval = 30  # Take screenshot every 30 seconds
last_screenshot_time = time.time()
productivity_message = ""
productivity_message_time = 0
productivity_message_duration = 5  # Show message for 5 seconds
openai_api_key = os.getenv('OPENAI_API_KEY')  # Get API key from environment variable DO NOT SHARE THIS KEY WITH ANYONE

def take_screenshot():
    """Take a screenshot, resize to 720p, and return the image as base64 string"""
    try:
        screenshot = ImageGrab.grab()
        
        # Resize to 720p (1280x720) while maintaining aspect ratio (Saves tokens on API calls)
        target_width = 1280
        target_height = 720
        
        # Calculate new dimensions maintaining aspect ratio
        original_width, original_height = screenshot.size
        aspect_ratio = original_width / original_height
        target_aspect_ratio = target_width / target_height
        
        if aspect_ratio > target_aspect_ratio:
            # Image is wider than target, fit to width
            new_width = target_width
            new_height = int(target_width / aspect_ratio)
        else:
            # Image is taller than target, fit to height
            new_height = target_height
            new_width = int(target_height * aspect_ratio)
        
        # Resize the image
        resized_screenshot = screenshot.resize((new_width, new_height), Image.LANCZOS)
        
        # Save temporarily and convert to base64
        temp_path = "temp_screenshot.png"
        resized_screenshot.save(temp_path, optimize=True, quality=85)
        
        with open(temp_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Clean up temp file
        os.remove(temp_path)
        return encoded_string
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

def analyze_productivity_with_chatgpt(image_base64):
    """Send screenshot to ChatGPT for productivity analysis"""
    if not openai_api_key:
        return "Error: OpenAI API key not found. Please set OPENAI_API_KEY environment variable."
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Create the API call using the OpenAI library
        response = client.chat.completions.create(
            model="gpt-4.1-mini",  
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this screenshot and determine if the user is on a productive website/application or a non-productive one. Consider:\n- Work-related websites (email, documents, coding, etc.)\n- Educational content\n- Social media, entertainment, gaming, shopping\n\nRespond with only 'PRODUCTIVE' if the content is work/education related, or 'NON-PRODUCTIVE' if it's entertainment/social media. If you can't determine, respond with 'UNKNOWN'."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=50
        )
        
        # Extract the response content
        result = response.choices[0].message.content.strip()
        return result
            
    except Exception as e:
        return f"Error: {str(e)}"

def update_session_stats(bpm, is_productive, focus_score):
    """Update session statistics"""
    session_data['blink_count'] += 1 if bpm > 0 else 0
    session_data['productive_time'] += 1 if is_productive else 0
    session_data['distraction_count'] += 1 if not is_productive else 0
    session_data['focus_score_total'] += focus_score
    session_data['data_points'] += 1

def generate_session_report():
    """Generate a simple session report"""
    session_duration = time.time() - session_start_time
    avg_focus_score = session_data['focus_score_total'] / session_data['data_points'] if session_data['data_points'] > 0 else 0
    productivity_percentage = (session_data['productive_time'] / session_data['data_points'] * 100) if session_data['data_points'] > 0 else 0
    
    # Create session folder
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = f"reports/session_{session_id}"
    os.makedirs(session_folder, exist_ok=True)
    
    # Generate report
    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              FOCUSON SESSION REPORT                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

📊 SESSION SUMMARY:
   • Duration: {session_duration/60:.1f} minutes
   • Total Blinks: {session_data['blink_count']}
   • Focus Score: {avg_focus_score:.1f}/100
   • Productivity: {productivity_percentage:.1f}%
   • Distractions: {session_data['distraction_count']}

🎯 PERFORMANCE:
"""
    
    if avg_focus_score >= 80:
        report += "   • 🎉 Excellent focus maintained!\n"
    elif avg_focus_score >= 60:
        report += "   • 👍 Good focus with room for improvement\n"
    else:
        report += "   • 📉 Focus needs improvement\n"
    
    if productivity_percentage >= 80:
        report += "   • 🎯 High productivity achieved\n"
    elif productivity_percentage >= 60:
        report += "   • 📊 Moderate productivity\n"
    else:
        report += "   • ⚠️  Low productivity - consider environment changes\n"
    
    report += f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                              END OF REPORT                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    
    # Save report
    report_file = f"{session_folder}/report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save session data
    data_file = f"{session_folder}/session_data.json"
    session_data['end_time'] = time.time()
    session_data['duration'] = session_duration
    session_data['avg_focus_score'] = avg_focus_score
    session_data['productivity_percentage'] = productivity_percentage
    
    with open(data_file, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"\n📁 Session data saved to: {session_folder}/")
    print(f"📄 Report: {report_file}")
    print(f"📊 Data: {data_file}")
    print(report)

while True:
    _, frame = webcam.read()
    gaze.refresh(frame)

    new_frame = gaze.annotated_frame()
    text = ""

    # Blink detection and counting
    current_time = time.time()
    elapsed_time = current_time - blink_start_time
    
    if gaze.is_blinking():
        if not is_blinking_state:  # New blink detected
            blink_count += 1
            last_blink_time = current_time
            is_blinking_state = True
    else:
        is_blinking_state = False

    # Calculate blinks per minute
    if elapsed_time >= 60:  # Reset every minute
        blink_count = 0
        blink_start_time = current_time
        elapsed_time = 0
    
    # Calculate current BPM (blinks per minute)
    if elapsed_time > 0:
        bpm = (blink_count / elapsed_time) * 60
    else:
        bpm = 0

    # Baseline establishment (first 30 seconds)
    if not baseline_established:
        baseline_elapsed = current_time - baseline_start_time
        if baseline_elapsed >= baseline_duration:
            # Calculate baseline BPM from the first 30 seconds
            baseline_bpm = (blink_count / baseline_elapsed) * 60
            baseline_established = True
            print(f"Baseline BPM established: {baseline_bpm:.1f}")

    # Monitor for significant changes from baseline
    if baseline_established and bpm > 0:
        change_percentage = abs(bpm - baseline_bpm) / baseline_bpm * 100
        if change_percentage >= 40:  # 40% change threshold (could be 30% to be more realistic)
            if bpm > baseline_bpm:
                change_message = "Increased Blinking Rate"
            else:
                change_message = "Decreased Blinking Rate"
            change_message_time = current_time

    # Clear change message after duration
    if current_time - change_message_time > change_message_duration:
        change_message = ""

    # Eye contact tracking
    if gaze.is_right() or gaze.is_left():
        # User is looking away from center
        if looking_away_start_time is None:
            looking_away_start_time = current_time
        else:
            # Check if they've been looking away for more than threshold
            time_looking_away = current_time - looking_away_start_time
            if time_looking_away >= eye_contact_threshold:
                eye_contact_message = "User has lost eye contact with screen"
                eye_contact_message_time = current_time
    else:
        # User is looking at center (or eyes not detected)
        looking_away_start_time = None

    # Clear eye contact message after duration
    if current_time - eye_contact_message_time > eye_contact_message_duration:
        eye_contact_message = ""

    # Screenshot and productivity analysis (every 30 seconds)
    if current_time - last_screenshot_time >= screenshot_interval:
        print("Taking screenshot for productivity analysis...")
        screenshot_base64 = take_screenshot()
        
        if screenshot_base64:
            print("Analyzing screenshot with ChatGPT...")
            analysis_result = analyze_productivity_with_chatgpt(screenshot_base64)
            
            if "NON-PRODUCTIVE" in analysis_result.upper():
                productivity_message = f"Non-productive activity detected: {analysis_result}"
            elif "ERROR" in analysis_result.upper():
                productivity_message = f"Analysis error: {analysis_result}"
            elif "UNKNOWN" in analysis_result.upper():
                productivity_message = "Unable to determine productivity level"
            else:
                productivity_message = "Productive activity confirmed"
            
            productivity_message_time = current_time
            print(f"Productivity analysis result: {analysis_result}")
        
        last_screenshot_time = current_time

    # Clear productivity message after duration
    if current_time - productivity_message_time > productivity_message_duration:
        productivity_message = ""

    # Update persistent focus score (penalties applied only once per event)
    time_since_update = current_time - last_score_update
    
    # Check for blink rate changes and apply penalty only once
    if baseline_established and bpm > 0:
        change_percentage = abs(bpm - baseline_bpm) / baseline_bpm * 100
        if change_percentage >= 40 and not blink_penalty_applied:
            focus_score -= 5  # Apply penalty only once
            blink_penalty_applied = True
        elif change_percentage < 40:
            blink_penalty_applied = False  # Reset flag when condition improves
    
    # Check for eye contact issues and apply penalty only once
    if looking_away_start_time is not None:
        time_looking_away = current_time - looking_away_start_time
        if time_looking_away >= eye_contact_threshold and not eye_contact_penalty_applied:
            focus_score -= 3  # Apply penalty only once
            eye_contact_penalty_applied = True
        elif time_looking_away < eye_contact_threshold:
            eye_contact_penalty_applied = False  # Reset flag when looking back
    
    # Check for productivity issues and apply penalty only once
    if "NON-PRODUCTIVE" in productivity_message and not productivity_penalty_applied:
        focus_score -= 8  # Apply penalty only once
        productivity_penalty_applied = True
    elif "NON-PRODUCTIVE" not in productivity_message:
        productivity_penalty_applied = False  # Reset flag when productivity improves
    
    # Gradual score recovery over time (when no penalties are active)
    if (baseline_established and bpm > 0 and abs(bpm - baseline_bpm) / baseline_bpm * 100 < 40) and \
       (looking_away_start_time is None or current_time - looking_away_start_time < eye_contact_threshold) and \
       "NON-PRODUCTIVE" not in productivity_message:
        # Score recovers slowly when conditions are good
        focus_score += focus_score_decay_rate * time_since_update
    
    # Clamp score between 0 and 100
    focus_score = max(0, min(100, focus_score))
    last_score_update = current_time
    
    port = "/dev/cu.usbmodem1103"
    ser = serial.Serial(port, 9600)
    
    def score_to_color(score):
        if score >= 70:
            return "green"
        elif score >= 30:
            return "yellow"
        else:
            return "red"

    def send_color(score):
        color = score_to_color(score)
        ser.write((color + "\n").encode())
        
    send_color(focus_score)

    # Update session statistics (every 5 seconds)
    if session_data['data_points'] == 0 or current_time - session_start_time - (session_data['data_points'] * 5) >= 5:
        is_productive = "PRODUCTIVE" in productivity_message
        update_session_stats(bpm, is_productive, focus_score)

    # Gaze direction detection
    if gaze.is_right():
        text = "Looking right"
    elif gaze.is_left():
        text = "Looking left"
    elif gaze.is_center():
        text = "Looking center"

    # Helper function to draw rounded rectangle with transparency
    def draw_rounded_rect_with_bg(frame, text, position, font_scale, color, thickness, bg_color=(0, 0, 0), bg_alpha=0.3):
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, font_scale, thickness)
        
        # Calculate rectangle dimensions with padding
        padding = 10
        rect_width = text_width + 2 * padding
        rect_height = text_height + 2 * padding
        
        # Rectangle coordinates
        x, y = position
        rect_x1, rect_y1 = x - padding, y - text_height - padding
        rect_x2, rect_y2 = x + text_width + padding, y + padding
        
        # Draw semi-transparent background rectangle
        overlay = frame.copy()
        cv2.rectangle(overlay, (rect_x1, rect_y1), (rect_x2, rect_y2), bg_color, -1)
        cv2.addWeighted(overlay, bg_alpha, frame, 1 - bg_alpha, 0, frame)
        
        # Draw text
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_DUPLEX, font_scale, color, thickness)
    
    # Display gaze direction
    draw_rounded_rect_with_bg(new_frame, text, (60, 60), 2, (255, 0, 0), 2, (0, 0, 0), 0.3)
    
    # Display blink information
    draw_rounded_rect_with_bg(new_frame, f"Blinks: {blink_count}", (60, 120), 1, (0, 255, 0), 2, (0, 0, 0), 0.3)
    draw_rounded_rect_with_bg(new_frame, f"BPM: {bpm:.1f}", (60, 160), 1, (0, 255, 0), 2, (0, 0, 0), 0.3)
    draw_rounded_rect_with_bg(new_frame, f"Time: {elapsed_time:.1f}s", (60, 200), 1, (0, 255, 0), 2, (0, 0, 0), 0.3)
    
    # Display baseline information
    if baseline_established:
        draw_rounded_rect_with_bg(new_frame, f"Baseline: {baseline_bpm:.1f} BPM", (60, 240), 1, (255, 255, 0), 2, (0, 0, 0), 0.3)
    else:
        baseline_remaining = baseline_duration - (current_time - baseline_start_time)
        draw_rounded_rect_with_bg(new_frame, f"Establishing baseline: {baseline_remaining:.0f}s", (60, 240), 1, (255, 255, 0), 2, (0, 0, 0), 0.3)
    
    # Display change message
    if change_message:
        draw_rounded_rect_with_bg(new_frame, change_message, (60, 280), 1.5, (0, 0, 255), 2, (0, 0, 0), 0.3)
    
    # Display eye contact message
    if eye_contact_message:
        draw_rounded_rect_with_bg(new_frame, eye_contact_message, (60, 320), 1.5, (255, 0, 255), 2, (0, 0, 0), 0.3)
    
    # Display productivity message
    if productivity_message:
        draw_rounded_rect_with_bg(new_frame, productivity_message, (60, 360), 1, (0, 255, 255), 2, (0, 0, 0), 0.3)
    
    # Display focus score
    draw_rounded_rect_with_bg(new_frame, f"Focus Score: {focus_score:.0f}", (60, 400), 1.2, (255, 255, 255), 2, (0, 0, 0), 0.3)
    
    cv2.imshow("FocusON - Productivity Monitor", new_frame)

    if cv2.waitKey(1) == 27:
        print("\n" + "="*60)
        print("SESSION ENDED - GENERATING REPORT...")
        print("="*60)
        generate_session_report()
        break