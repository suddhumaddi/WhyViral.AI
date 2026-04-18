from modules.transcribe import transcribe_video
from modules.analyzer import analyze_transcript

# Step 1: Get transcript from video
transcript = transcribe_video("sample.mp4")

# Step 2: Analyze for viral segments
segments = analyze_transcript(transcript)

# Step 3: Print results
print("\n=== VIRAL SEGMENTS ===")
for seg in segments:
    print(seg)