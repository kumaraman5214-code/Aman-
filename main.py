import os
import json
import asyncio
import edge_tts
import requests
from moviepy.editor import *
from google import genai
from pexels_api import PexelsAPI
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import random

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pexels = PexelsAPI(os.getenv("PEXELS_API_KEY"))

# Civil Engineering ke trending topics (2026 ke hisab se)
CIVIL_TOPICS = [
    "AI Revolution in Civil Engineering 2026",
    "Modular Construction aur Prefabrication ki Kranti",
    "Sustainable Infrastructure aur Green Building Trends",
    "BIM vs Civil 3D 2026 - Kya Naya Aaya?",
    "Digital Twins in Smart Cities",
    "Drone aur LiDAR se Construction ka Future",
    "Climate Resilient Infrastructure kaise banaye",
    "Data Centers ke liye Civil Engineering Challenges",
    "3D Printing in Construction - Real Examples",
    "Autonomous Construction Machines aur Robotics"
]

def get_random_civil_topic():
    return random.choice(CIVIL_TOPICS)

def generate_script(topic):
    prompt = f"""You are a professional Civil Engineering YouTube Shorts creator.
Topic: {topic} (Hindi + English mix mein energetic style)

Return ONLY valid JSON:
{{
  "title": "Very catchy title under 65 characters",
  "description": "Full description with emojis, hashtags like #CivilEngineering #Construction #AIinCivil aur strong CTA",
  "tags": ["CivilEngineering", "Construction", "Trending"],
  "scenes": [
    {{"text": "Narration line with energy", "duration": 8, "visual_prompt": "Civil engineering related B-roll description"}}
  ]
}}
First 3 seconds mein strong hook ho."""
    
    response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt])
    text = response.text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    return json.loads(text)

def generate_thumbnail(title, topic):
    prompt = f"""Highly clickable YouTube Shorts thumbnail 1280x720 for Civil Engineering video:
Title: {title}
Topic: {topic}

- Big bold text (white/yellow with black outline)
- Construction site, modern building, drone view, AI elements
- Bright energetic colors, professional civil engineering feel
- Add text like "2026 Revolution" or "Future of Civil" """

    response = client.models.generate_images(
        model="gemini-3.1-flash-image-preview",
        prompt=prompt,
        number_of_images=1
    )
    image = response.images[0]
    image.save("thumbnail.jpg")
    print("✅ Civil Engineering Thumbnail ban gaya!")
    return "thumbnail.jpg"

async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")  # Natural Hindi voice
    await communicate.save("voice.mp3")

def create_video(scenes):
    # ... (same as before - video + clips + voice)
    video_clips = []
    audio_clips = []
    for i, scene in enumerate(scenes):
        asyncio.run(text_to_speech(scene['text']))
        audio = AudioFileClip("voice.mp3").set_duration(scene.get('duration', 8))
        audio_clips.append(audio)

        try:
            videos = pexels.search_videos(query=scene['visual_prompt'] + " civil engineering construction", per_page=1)
            if videos and videos.get('videos'):
                url = videos['videos'][0]['video_files'][0]['link']
                r = requests.get(url, timeout=15)
                with open(f"clip_{i}.mp4", "wb") as f:
                    f.write(r.content)
                clip = VideoFileClip(f"clip_{i}.mp4").subclip(0, scene.get('duration', 8))
                video_clips.append(clip)
        except:
            video_clips.append(ColorClip(size=(1280,720), color=(0,0,0), duration=scene.get('duration', 8)))

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_audio = concatenate_audioclips(audio_clips)
    final_video = final_video.set_audio(final_audio)
    final_video.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac")
    return "final_video.mp4"

if __name__ == "__main__":
    topic = os.getenv("VIDEO_TOPIC", get_random_civil_topic())
    print(f"🚀 Civil Engineering Video ban raha hai: {topic}")

    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"], topic)
    video_file = create_video(script["scenes"])

    print("✅ Civil Engineering Video + Thumbnail ready!")
    print(f"Title: {script['title']}")
