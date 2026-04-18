# Required installations:
# pip install moviepy

import os
from moviepy.editor import VideoFileClip
from streamlit import video

CLIPS_DIR = "outputs/clips"


def clip_video(video_path: str, segments: list[dict]) -> list[str]:
    """
    Cut a video into clips based on provided timestamp segments.

    Args:
        video_path: Path to the source video file.
        segments:   List of dicts with "start" and "end" keys (in seconds).
                    e.g. [{"start": 0.0, "end": 30.5}, ...]

    Returns:
        List of file paths for the saved clips.
        e.g. ["outputs/clips/clip_1.mp4", "outputs/clips/clip_2.mp4"]

    Raises:
        FileNotFoundError: If the source video does not exist.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Ensure output directory exists
    os.makedirs(CLIPS_DIR, exist_ok=True)

    output_paths = []

    # Load the full video once and reuse for all clips
    print(f"[clipper] Loading video: {video_path}")
    video = VideoFileClip(video_path)
    video_duration = video.duration

    try:
        for idx, segment in enumerate(segments, start=1):
            start = segment.get("start")
            end   = segment.get("end")

            # ── Validate timestamps ─────────────────────────────────────
            if start is None or end is None:
                print(f"[clipper] Segment {idx}: missing 'start' or 'end' — skipping.")
                continue

            if start < 0 or end < 0:
                print(f"[clipper] Segment {idx}: negative timestamps ({start}–{end}) — skipping.")
                continue

            if start >= end:
                print(f"[clipper] Segment {idx}: start ({start}) >= end ({end}) — skipping.")
                continue

            if start >= video_duration:
                print(f"[clipper] Segment {idx}: start ({start}s) beyond video length ({video_duration:.2f}s) — skipping.")
                continue

            # Clamp end to video duration if it overshoots
            if end > video_duration:
                print(f"[clipper] Segment {idx}: end ({end}s) clamped to video duration ({video_duration:.2f}s).")
                end = video_duration

            # ── Cut and save clip ───────────────────────────────────────
            output_path = os.path.join(CLIPS_DIR, f"clip_{idx}.mp4")

            print(f"[clipper] Cutting clip {idx}: {start}s → {end}s  →  {output_path}")
            clip = video.subclip(start, end)

            # 🔥 FORCE AUDIO ATTACH
            if video.audio is not None:
                clip = clip.set_audio(video.audio.subclip(start, end))
            clip.write_videofile(
                output_path,
                codec="libx264",
                audio=False,          # set to True if you want to keep audio (requires ffmpeg)
                logger=None,         # suppress verbose MoviePy output
            )
            clip.close()

            output_paths.append(output_path)

    finally:
        # Always release the video resource
        video.close()

    print(f"[clipper] Done — {len(output_paths)} clip(s) saved to '{CLIPS_DIR}/'")
    return output_paths


# ---------------------------------------------------------------------------
# Quick smoke-test — run with:  python clipper.py <video_path>
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "sample.mp4"

    # Example segments (swap in real output from analyzer.py)
    test_segments = [
        {"start": 0.0,  "end": 15.0},
        {"start": 22.0, "end": 45.0},
        {"start": 50.0, "end": 75.0},
    ]

    saved_clips = clip_video(path, test_segments)
    print("\nSaved clips:")
    for p in saved_clips:
        print(f"  {p}")