from modules.transcribe import transcribe_video
from modules.analyzer import analyze_transcript
from modules.enhancer import enhance_clip

video_path = "sample.mp4"

transcript = transcribe_video(video_path)
segments = analyze_transcript(transcript)

print("\n=== ENHANCED OUTPUT ===")

for seg in segments:
    text = " ".join(
        s["text"] for s in transcript
        if s["start"] >= seg["start"] and s["end"] <= seg["end"]
    )

    result = enhance_clip(text)

    print("\n--- CLIP ---")
    print("TEXT:", text[:100], "...")
    print("SCORE:", result["score"])
    print("REASONS:", result["reason"])
    print("HOOK:", result["hook"])
    print("CAPTION:", result["caption"])
    print("TIPS:", result["tips"])