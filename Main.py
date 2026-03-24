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

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
pexels = PexelsAPI(os.getenv("PEXELS_API_KEY"))

def generate_script(topic):
    prompt = f"""Viral YouTube Shorts script banao topic: {topic}
Sirf valid JSON return karo:
{{
  "title": "Catchy short title",
  "description": "Description + hashtags + CTA",
  "tags": ["motivation", "shorts"],
  "scenes": [
    {{"text": "Narration line yahan", "duration": 8, "visual_prompt": "Background video ke liye description"}}
  ]
}}"""
    response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt])
    text = response.text.strip()
    if text.startswith("```json"): 
        text = text[7:-3].strip()
    return json.loads(text)

def generate_thumbnail(title, topic):
    prompt = f"""Viral YouTube Shorts thumbnail 1280x720 banao:
Title: {title}
Topic: {topic}
Big bold text, bright colors, emotional face, high contrast, professional viral style."""
    
    response = client.models.generate_images(
        model="gemini-3.1-flash-image-preview",
        prompt=prompt,
        number_of_images=1
    )
    image = response.images[0]
    image.save("thumbnail.jpg")
    print("✅ Thumbnail ban gaya!")
    return "thumbnail.jpg"

async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, "hi-IN-Neural2-A")
    await communicate.save("voice.mp3")

def create_video(scenes):
    video_clips = []
    audio_clips = []
    for i, scene in enumerate(scenes):
        asyncio.run(text_to_speech(scene['text']))
        audio = AudioFileClip("voice.mp3").set_duration(scene.get('duration', 8))
        audio_clips.append(audio)
        
        try:
            videos = pexels.search_videos(query=scene['visual_prompt'], per_page=1)
            if videos and videos.get('videos'):
                url = videos['videos'][0]['video_files'][0]['link']
                r = requests.get(url)
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
    topic = os.getenv("VIDEO_TOPIC", "Motivational story about never giving up")
    print("🚀 Video ban raha hai topic pe:", topic)
    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"], topic)
    video_file = create_video(script["scenes"])
    print("✅ Video aur Thumbnail ready ho gaya!")
    print("Upload part abhi band hai. Test ke baad on kar denge.")
