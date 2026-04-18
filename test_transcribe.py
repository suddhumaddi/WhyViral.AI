from modules.transcribe import transcribe_video

segments = transcribe_video("sample.mp4")
print(segments[:3])