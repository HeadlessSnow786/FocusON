# FocusON Reports

This folder contains all your FocusON session data and reports.

## Folder Structure

Each session creates a folder with the format: `session_YYYYMMDD_HHMMSS/`

For example: `session_20241201_143022/` (December 1st, 2024 at 2:30:22 PM)

## Files in Each Session Folder

- **`report.txt`** - Human-readable session summary with performance insights
- **`session_data.json`** - Raw session data in JSON format for analysis

## Comparing Sessions

To compare multiple sessions, run:

```bash
python compare_sessions.py
```

This will analyze all sessions in the reports folder and show:
- Individual session statistics
- Progress over time
- Focus and productivity improvements

## Session Data Format

The `session_data.json` file contains:

```json
{
  "start_time": 1701441022.123,
  "end_time": 1701441322.456,
  "duration": 300.333,
  "blink_count": 45,
  "productive_time": 280,
  "distraction_count": 20,
  "focus_score_total": 7500,
  "data_points": 60,
  "avg_focus_score": 75.0,
  "productivity_percentage": 85.0
}
```

## Tips

- Keep this folder for long-term progress tracking
- Use the comparison tool to see if your focus is improving
- The focus score ranges from 0-100 (higher is better)
- Productivity percentage shows time spent on productive activities 