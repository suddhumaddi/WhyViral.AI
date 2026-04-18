from modules.transcribe import transcribe_video
from modules.analyzer import analyze_transcript
from modules.clipper import clip_video

video_path = "sample.mp4"

# Step 1: Transcribe
transcript = transcribe_video(video_path)

# Step 2: Analyze
segments = analyze_transcript(transcript)

print("\nSegments:")
for s in segments:
    print(s)

# Step 3: Clip video
clips = clip_video(video_path, segments)

print("\nGenerated Clips:")
for c in clips:
    print(c)