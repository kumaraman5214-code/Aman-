import os
import json
import asyncio
import edge_tts
import requests
from moviepy.editor import *
from google import genai
from huggingface_hub import InferenceClient
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import random
import time

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
hf_client = InferenceClient(token=os.getenv("HUGGINGFACE_API_TOKEN"))

# Civil Engineering Topics
CIVIL_TOPICS = [
    "AI Revolution in Civil Engineering 2026",
    "Modular Construction aur Prefabrication ki Kranti",
    "Sustainable Green Building Trends 2026",
    "BIM vs Civil 3D Future",
    "Digital Twins in Smart Cities",
    "Drone LiDAR in Construction",
    "Climate Resilient Infrastructure"
]

def get_random_civil_topic():
    return random.choice(CIVIL_TOPICS)

def generate_script(topic):
    prompt = f"""Professional Civil Engineering YouTube Shorts creator.
Topic: {topic}

Return ONLY valid JSON:
{{
  "title": "Catchy title under 65 chars",
  "description": "Description with emojis + hashtags #CivilEngineering",
  "tags": ["CivilEngineering", "Construction"],
  "scenes": [
    {{"text": "Energetic narration", "duration": 7, "visual_prompt": "Civil engineering scene description"}}
  ]
}}"""
    response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt])
    text = response.text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    return json.loads(text)

def generate_thumbnail(title, topic):
    prompt = f"""Viral YouTube Shorts thumbnail 1280x720 Civil Engineering:
Title: {title}
- Big bold text, construction site, modern building, AI elements, bright colors"""
    response = client.models.generate_images(model="gemini-3.1-flash-image-preview", prompt=prompt, number_of_images=1)
    image = response.images[0]
    image.save("thumbnail.jpg")
    print("✅ Thumbnail ready!")
    return "thumbnail.jpg"

async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save("voice.mp3")

def generate_hf_video_clip(visual_prompt, duration=6):
    """Hugging Face se AI video clip generate (short clip)"""
    try:
        # Example: CogVideoX ya Mochi model use karo (free inference)
        # Note: Real mein slow ho sakta hai, timeout set karo
        video_bytes = hf_client.text_to_video(
            prompt=visual_prompt + ", civil engineering construction site, realistic, 4k",
            model="zai-org/CogVideoX-5b",   # ya "genmo/mochi-1-preview" try kar sakte ho
            num_frames=48,  # \~6 seconds @ 8fps
        )
        filename = "hf_clip.mp4"
        with open(filename, "wb") as f:
            f.write(video_bytes)
        clip = VideoFileClip(filename).subclip(0, min(duration, VideoFileClip(filename).duration))
        return clip
    except Exception as e:
        print("HF video failed:", e)
        # Fallback: black screen
        return ColorClip(size=(1280, 720), color=(0,0,0), duration=duration)

def create_video(scenes):
    video_clips = []
    audio_clips = []
    for i, scene in enumerate(scenes):
        asyncio.run(text_to_speech(scene['text']))
        audio = AudioFileClip("voice.mp3").set_duration(scene.get('duration', 7))
        audio_clips.append(audio)

        # Hugging Face se AI clip try karo
        clip = generate_hf_video_clip(scene['visual_prompt'])
        video_clips.append(clip)

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_audio = concatenate_audioclips(audio_clips)
    final_video = final_video.set_audio(final_audio)
    final_video.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final_video.mp4"

if __name__ == "__main__":
    topic = os.getenv("VIDEO_TOPIC", get_random_civil_topic())
    print(f"🚀 Civil Engineering Video: {topic}")

    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"], topic)
    video_file = create_video(script["scenes"])

    print("✅ Video + Thumbnail ready!")
