import streamlit as st
import moviepy.editor as mp
import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS
import tempfile
import os

st.title("🎥 Multilingual Video Translator")

uploaded_video = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
language_options = {"Hindi": "hi", "Kannada": "kn", "Telugu": "te", "Tamil": "ta", "French": "fr"}
target_language = st.selectbox("Choose target language", list(language_options.keys()))

if uploaded_video:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        tmp_video.write(uploaded_video.read())
        video_path = tmp_video.name

    st.video(video_path)
    st.write("Extracting audio...")

    # Extract audio
    video_clip = mp.VideoFileClip(video_path)
    audio_path = video_path.replace(".mp4", ".wav")
    video_clip.audio.write_audiofile(audio_path)

    st.success("Audio extracted. Starting transcription...")

    # Transcribe
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    segments = result["segments"]

    st.success("Transcription completed.")

    # Translate
    st.write("Translating segments...")
    translated_segments = []
    for seg in segments:
        translated_text = GoogleTranslator(source='auto', target=language_options[target_language]).translate(seg['text'])
        translated_segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "original": seg["text"],
            "translated": translated_text
        })

    # Generate translated clips
    st.write("Generating translated speech...")
    audio_clips = []

    for idx, seg in enumerate(translated_segments):
        tts = gTTS(seg["translated"], lang=language_options[target_language])
        temp_path = os.path.join(tempfile.gettempdir(), f"seg_{idx}.mp3")
        tts.save(temp_path)
        clip = mp.AudioFileClip(temp_path).set_start(seg["start"]).set_duration(seg["end"] - seg["start"])
        audio_clips.append(clip)

    # Combine all audio clips
    final_audio = mp.CompositeAudioClip(audio_clips).set_duration(video_clip.duration)

    st.success("✅ Translated audio generated with original timing!")

    # Replace original audio in video
    st.write("Replacing original video audio with translated version...")
    final_video_path = video_path.replace(".mp4", f"_{language_options[target_language]}_dubbed.mp4")
    final_video = video_clip.set_audio(final_audio)
    final_video.write_videofile(final_video_path, codec="libx264", audio_codec="aac")

    st.success("🎬 Final dubbed video generated!")
    st.video(final_video_path)
