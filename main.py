import os
import json
import asyncio
import edge_tts
import random
from moviepy.editor import *
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import pickle
from PIL import Image, ImageDraw

# ===================== CONFIG =====================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    try:
        print("🤖 Gemini se script generate kar raha hoon...")
        prompt = f"""Professional Civil Engineering YouTube Shorts creator.
Topic: {topic}

Return ONLY valid JSON:
{{
  "title": "Catchy title under 65 chars",
  "description": "Full description + emojis + hashtags #CivilEngineering",
  "tags": ["CivilEngineering", "Construction"],
  "scenes": [
    {{"text": "Energetic narration line", "duration": 7}}
  ]
}}"""
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:-3].strip()
        script = json.loads(text)
        print("✅ Gemini se script ban gaya!")
        return script
    except:
        print("⚠️ Gemini quota khatam → Fallback mode")
        return {
            "title": f"{topic} - Important Facts 🔥",
            "description": f"{topic} ke baare mein sab kuch. Civil Engineering ke liye must watch! #CivilEngineering",
            "tags": ["CivilEngineering", "Construction"],
            "scenes": [
                {"text": f"Dosto, aaj baat karte hain {topic} ki!", "duration": 7},
                {"text": "Yeh technology bahut tezi se badal rahi hai.", "duration": 7},
                {"text": "Comment mein apna opinion zaroor batao!", "duration": 6}
            ]
        }

def generate_thumbnail(title):
    img = Image.new('RGB', (1280, 720), color=(0, 70, 130))
    draw = ImageDraw.Draw(img)
    draw.text((100, 280), title[:60], fill=(255, 255, 255))
    img.save("thumbnail.jpg")
    print("✅ Thumbnail ban gaya!")
    return "thumbnail.jpg"

async def text_to_speech(text):
    communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural")
    await communicate.save("voice.mp3")

def create_video(scenes):
    audio_clips = []
    video_clips = []

    for scene in scenes:
        asyncio.run(text_to_speech(scene['text']))
        audio = AudioFileClip("voice.mp3")
        audio_clips.append(audio)

        duration = audio.duration if audio.duration > 0 else 7
        clip = ColorClip(size=(1280, 720), color=(0,0,0), duration=duration)
        video_clips.append(clip)

    final_audio = concatenate_audioclips(audio_clips)
    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video = final_video.set_audio(final_audio)

    final_video.write_videofile("final_video.mp4", fps=24, codec="libx264", audio_codec="aac",
                                temp_audiofile="temp-audio.m4a", remove_temp=True, threads=2)
    print("✅ Video ban gaya!")
    return "final_video.mp4"

def get_youtube_service():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        print("🔄 YouTube token refresh kar raha hoon...")
        try:
            creds = Credentials(
                None,
                refresh_token=os.getenv("YOUTUBE_REFRESH_TOKEN"),
                token_uri="https://oauth2.googleapis.com/token",
                scopes=SCOPES
            )
            creds.refresh(Request())
            print("✅ Token refresh successful!")
        except Exception as e:
            print("❌ Token refresh failed:", str(e))
            raise

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

    print(f"🎉 Video uploaded successfully! Video ID: {response['id']}")

if __name__ == "__main__":
    topic = os.getenv("VIDEO_TOPIC", get_random_topic())
    print(f"🚀 Starting Civil Engineering Shorts: {topic}")

    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"])
    video_file = create_video(script["scenes"])

    upload_to_youtube(
        video_file,
        script["title"],
        script["description"],
        script["tags"],
        thumbnail_file
    )
    print("✅ Sab complete!")
