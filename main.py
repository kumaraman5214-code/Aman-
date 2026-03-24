import os
import json
import asyncio
import edge_tts
import requests
import random
from moviepy.editor import *
from google import genai
from huggingface_hub import InferenceClient
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
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
  "description": "Full description + emojis + hashtags #CivilEngineering #Construction",
  "tags": ["CivilEngineering", "Construction", "Trending"],
  "scenes": [
    {{"text": "Energetic narration line", "duration": 7, "visual_prompt": "Civil engineering construction scene"}}
  ]
}}"""
    response = client.models.generate_content(model="gemini-2.0-flash", contents=[prompt])
    text = response.text.strip()
    if text.startswith("```json"): text = text[7:-3].strip()
    return json.loads(text)

def generate_thumbnail(title, topic):
    prompt = f"""Viral YouTube Shorts thumbnail 1280x720 Civil Engineering:
Title: {title}
Bright colors, construction site, modern building, AI elements, big bold text"""
    response = client.models.generate_images(model="gemini-3.1-flash-image-preview", prompt=prompt, number_of_images=1)
    image = response.images[0]
    image.save("thumbnail.jpg")
    print("✅ Thumbnail ready!")
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
            # Hugging Face se short AI clip
            video_bytes = hf_client.text_to_video(prompt=scene['visual_prompt'] + ", realistic civil engineering construction site", model="zai-org/CogVideoX-5b")
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

def get_youtube_service():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secret = json.loads(os.getenv("YOUTUBE_CLIENT_SECRET"))
            creds = Credentials(
                None,
                refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_secret["installed"]["client_id"],
                client_secret=client_secret["installed"]["client_secret"],
                scopes=SCOPES
            )
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build("youtube", "v3", credentials=creds)

def upload_to_youtube(video_file, title, description, tags, thumbnail_file):
    youtube = get_youtube_service()
    body = {
        'snippet': {'title': title, 'description': description, 'tags': tags, 'categoryId': '22'},
        'status': {'privacyStatus': 'public'}
    }
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()

    if os.path.exists(thumbnail_file):
        thumb_media = MediaFileUpload(thumbnail_file, mimetype='image/jpeg')
        youtube.thumbnails().set(videoId=response['id'], media_body=thumb_media).execute()
        print("✅ Thumbnail set ho gaya!")

    print(f"🎉 Video uploaded successfully! ID: {response['id']}")

if __name__ == "__main__":
    topic = os.getenv("VIDEO_TOPIC", get_random_topic())
    print(f"🚀 Generating Civil Engineering Shorts: {topic}")

    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"], topic)
    video_file = create_video(script["scenes"])

    upload_to_youtube(
        video_file,
        script["title"],
        script["description"],
        script["tags"],
        thumbnail_file
    )
    print("✅ Sab complete! Video YouTube pe upload ho gaya.")
