import cv2
import time
import os
import base64
import requests
from PIL import ImageGrab, Image
from gaze_tracking import GazeTracking

gaze = GazeTracking()
webcam = cv2.VideoCapture(0)

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
openai_api_key = os.getenv('OPENAI_API_KEY')  # Get API key from environment variable

def take_screenshot():
    """Take a screenshot, resize to 720p, and return the image as base64 string"""
    try:
        screenshot = ImageGrab.grab()
        
        # Resize to 720p (1280x720) while maintaining aspect ratio
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
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_api_key}"
        }
        
        payload = {
            "model": "gpt-4.1-mini",
            "messages": [
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
            "max_tokens": 50
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()['choices'][0]['message']['content'].strip()
            return result
        else:
            return f"Error: API request failed with status {response.status_code}"
            
    except Exception as e:
        return f"Error: {str(e)}"

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
        if change_percentage >= 40:  # 40% change threshold
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

    # Gaze direction detection
    if gaze.is_right():
        text = "Looking right"
    elif gaze.is_left():
        text = "Looking left"
    elif gaze.is_center():
        text = "Looking center"

    # Display gaze direction
    cv2.putText(new_frame, text, (60, 60), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 0, 0), 2)
    
    # Display blink information
    cv2.putText(new_frame, f"Blinks: {blink_count}", (60, 120), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)
    cv2.putText(new_frame, f"BPM: {bpm:.1f}", (60, 160), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)
    cv2.putText(new_frame, f"Time: {elapsed_time:.1f}s", (60, 200), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0), 2)
    
    # Display baseline information
    if baseline_established:
        cv2.putText(new_frame, f"Baseline: {baseline_bpm:.1f} BPM", (60, 240), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 0), 2)
    else:
        baseline_remaining = baseline_duration - (current_time - baseline_start_time)
        cv2.putText(new_frame, f"Establishing baseline: {baseline_remaining:.0f}s", (60, 240), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 0), 2)
    
    # Display change message
    if change_message:
        cv2.putText(new_frame, change_message, (60, 280), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 255), 2)
    
    # Display eye contact message
    if eye_contact_message:
        cv2.putText(new_frame, eye_contact_message, (60, 320), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 0, 255), 2)
    
    # Display productivity message
    if productivity_message:
        cv2.putText(new_frame, productivity_message, (60, 360), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 255), 2)
    
    cv2.imshow("Demo", new_frame)

    if cv2.waitKey(1) == 27:
        break