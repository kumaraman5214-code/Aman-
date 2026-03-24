import os
import json
import asyncio
import edge_tts
import requests
import random
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ColorClip, concatenate_audioclips
import google.generativeai as genai
from huggingface_hub import InferenceClient
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
hf_client = InferenceClient(token=os.getenv("HUGGINGFACE_API_TOKEN"))

CIVIL_TOPICS = [
    "AI Revolution in Civil Engineering 2026",
    "Modular Construction ki Kranti",
    "Sustainable Green Buildings 2026",
    "Digital Twins in Smart Cities",
    "Drone & LiDAR in Construction",
    "Climate Resilient Infrastructure",
    "3D Printing in Civil Engineering"
]

def get_random_topic():
    return random.choice(CIVIL_TOPICS)

def generate_script(topic):
    prompt = f"""Professional Civil Engineering YouTube Shorts creator.
Topic: {topic}

Return ONLY valid JSON:
{{
  "title": "Catchy title under 65 chars",
  "description": "Full description + emojis + hashtags #CivilEngineering",
  "tags": ["CivilEngineering", "Construction"],
  "scenes": [
    {{"text": "Energetic narration line", "duration": 7, "visual_prompt": "Civil engineering construction scene"}}
  ]
}}"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    text = response.text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    return json.loads(text)

def generate_thumbnail(title, topic):
    prompt = f"""Viral YouTube Shorts thumbnail 1280x720 Civil Engineering:
Title: {title}
Bright colors, construction site, modern building, big bold text"""
    model = genai.GenerativeModel('gemini-3.1-flash-image-preview')  # Image generation
    response = model.generate_content(prompt)   # Note: Image generation may need different model in some cases
    # For now using text fallback - we'll fix image later if needed
    # Temporary: use simple text for thumbnail (we'll improve later)
    print("Thumbnail generation skipped for now (image model issue)")
    # Save a dummy thumbnail
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new('RGB', (1280, 720), color=(0, 100, 200))
    draw = ImageDraw.Draw(img)
    draw.text((100, 300), title, fill=(255,255,255))
    img.save("thumbnail.jpg")
    return "thumbnail.jpg"

async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save("voice.mp3")

def create_video(scenes):
    video_clips = []
    audio_clips = []
    for i, scene in enumerate(scenes):
        asyncio.run(text_to_speech(scene['text']))
        audio = AudioFileClip("voice.mp3").set_duration(scene.get('duration', 7))
        audio_clips.append(audio)

        try:
            video_bytes = hf_client.text_to_video(
                prompt=scene['visual_prompt'] + ", realistic civil engineering construction site, 4k",
                model="zai-org/CogVideoX-5b"
            )
            with open(f"clip_{i}.mp4", "wb") as f:
                f.write(video_bytes)
            clip = VideoFileClip(f"clip_{i}.mp4").subclip(0, 7)
            video_clips.append(clip)
        except:
            video_clips.append(ColorClip(size=(1280,720), color=(0,0,0), duration=7))

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_audio = concatenate_audioclips(audio_clips)
    final_video = final_video.set_audio(final_audio)
    final_video.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final_video.mp4"

# ... (baaki upload functions same as pehle wale)

# Main
if __name__ == "__main__":
    topic = os.getenv("VIDEO_TOPIC", get_random_topic())
    print(f"🚀 Generating: {topic}")

    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"], topic)
    video_file = create_video(script["scenes"])

    print("✅ Video ready!")
    # Upload code abhi comment hai taaki pehle yeh chal jaye
    # upload_to_youtube(...)
