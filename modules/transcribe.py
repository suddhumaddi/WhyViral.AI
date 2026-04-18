# Required installations:
# pip install openai-whisper
# pip install moviepy
# pip install torch  (CPU version: pip install torch --index-url https://download.pytorch.org/whl/cpu)

import os
import tempfile
import whisper
from moviepy.editor import VideoFileClip


def extract_audio(video_path: str, output_audio_path: str) -> str:
    """
    Extracts audio from a video file and saves it as a .wav file.

    Args:
        video_path: Path to the input video file.
        output_audio_path: Path where the extracted audio will be saved.

    Returns:
        Path to the extracted audio file.
    """
    clip = VideoFileClip(video_path)

    if clip.audio is None:
        clip.close()
        raise ValueError(f"No audio track found in video: {video_path}")

    clip.audio.write_audiofile(output_audio_path, logger=None)
    clip.close()
    return output_audio_path


def transcribe_video(video_path: str, model_size: str = "base") -> list[dict]:
    """
    Transcribes a video file using OpenAI Whisper.

    Supports direct audio files (.mp3, .wav, .m4a, etc.) or video files
    (.mp4, .mov, .avi, etc.) — audio is extracted automatically if needed.

    Args:
        video_path:  Path to the video (or audio) file.
        model_size:  Whisper model to use. Options: "tiny", "base", "small",
                     "medium", "large". Larger = more accurate, slower.

    Returns:
        A list of dicts with keys:
            - "start" (float): Segment start time in seconds.
            - "end"   (float): Segment end time in seconds.
            - "text"  (str):   Transcribed text for the segment.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the file has no audio track.
        RuntimeError: If transcription fails unexpectedly.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"File not found: {video_path}")

    audio_extensions = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac"}
    _, ext = os.path.splitext(video_path.lower())

    audio_path = video_path          # assume it's already audio-compatible
    tmp_file = None                  # track temp file so we can clean up

    try:
        # If it's a video file, extract the audio track first
        if ext not in audio_extensions:
            tmp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp_file.close()
            audio_path = extract_audio(video_path, tmp_file.name)

        # Load Whisper model
        print(f"[transcribe] Loading Whisper model: '{model_size}' ...")
        model = whisper.load_model(model_size)

        # Run transcription
        print(f"[transcribe] Transcribing: {video_path} ...")
        result = model.transcribe(audio_path, verbose=False)

        # Parse segments into the target output format
        segments = [
            {
                "start": round(seg["start"], 3),
                "end":   round(seg["end"],   3),
                "text":  seg["text"].strip(),
            }
            for seg in result.get("segments", [])
        ]

        print(f"[transcribe] Done — {len(segments)} segment(s) found.")
        return segments

    except Exception as exc:
        raise RuntimeError(f"Transcription failed: {exc}") from exc

    finally:
        # Clean up temporary audio file if we created one
        if tmp_file and os.path.exists(tmp_file.name):
            os.remove(tmp_file.name)


# ---------------------------------------------------------------------------
# Quick smoke-test — run with:  python transcribe.py <path/to/video.mp4>
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <video_path> [model_size]")
        print("       model_size defaults to 'base'")
        sys.exit(1)

    path = sys.argv[1]
    size = sys.argv[2] if len(sys.argv) > 2 else "base"

    segments = transcribe_video(path, model_size=size)
    print(json.dumps(segments, indent=2, ensure_ascii=False))