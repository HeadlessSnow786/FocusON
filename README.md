# FocusON

**FocusON** is a productivity and attention monitoring tool that uses webcam-based gaze tracking, blink analysis, and AI-powered screenshot analysis to help users stay focused and productive.

## Features

- **Gaze Tracking:** Detects if you are looking left, right, or center using your webcam.
- **Blink Analysis:** Tracks blinks per minute and alerts you if your blink rate changes significantly from your baseline.
- **Eye Contact Monitoring:** Notifies you if you look away from the screen for more than 5 seconds.
- **Productivity Screenshot Analysis:** Takes a screenshot every 30 seconds and uses ChatGPT (GPT-4 Vision) to determine if you are on a productive or non-productive website/application.
- **Real-Time Feedback:** Displays messages and alerts directly on the video feed.

## Requirements

- Python 3.8+
- Webcam
- OpenAI API key (for screenshot analysis)
- The following Python packages:
  - dlib
  - numpy
  - opencv-python
  - setuptools
  - Pillow
  - requests
  - openai

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

1. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your_openai_api_key_here"
   ```

2. **Run the main script:**
   ```bash
   python focus.py
   ```

3. **Follow the on-screen instructions and feedback.**

## Notes

- Screenshots are sent to OpenAI for productivity analysis. Be mindful of privacy.
- The system works best in well-lit environments with a clear view of your face.
- You can adjust thresholds and intervals in the code to suit your needs.
- Gaze Tracking powered by Antoine Lamé's library. [Check it out!](https://github.com/antoinelame/GazeTracking)

## License

MIT License
