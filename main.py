import os
import json
import asyncio
import edge_tts
import random
from moviepy.editor import *
import google.generativeai as genai
from PIL import Image, ImageDraw

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
        print("🤖 Gemini try kar raha hoon...")
        prompt = f"""Professional Civil Engineering Shorts.
Topic: {topic}
Return ONLY JSON with title, description, tags, scenes."""
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"): text = text[7:-3].strip()
        return json.loads(text)
    except:
        print("⚠️ Gemini quota khatam → Fallback")
        return {
            "title": f"{topic} - Must Know Facts 🔥",
            "description": f"{topic} ke baare mein important baatein. Civil Engineering ke liye must watch! #CivilEngineering",
            "tags": ["CivilEngineering", "Construction"],
            "scenes": [
                {"text": f"Dosto, aaj baat karte hain {topic} ki!", "duration": 7},
                {"text": "Yeh technology bahut tezi se badal rahi hai.", "duration": 7},
                {"text": "Comment mein apna opinion batao!", "duration": 6}
            ]
        }

def generate_thumbnail(title):
    img = Image.new('RGB', (1280, 720), color=(0, 70, 130))
    draw = ImageDraw.Draw(img)
    draw.text((100, 280), title[:60], fill=(255, 255, 255))
    img.save("thumbnail.jpg")
    print("✅ Thumbnail ready")
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
    return "final_video.mp4"

if __name__ == "__main__":
    topic = os.getenv("VIDEO_TOPIC", get_random_topic())
    print(f"🚀 Starting: {topic}")

    script = generate_script(topic)
    thumbnail_file = generate_thumbnail(script["title"])
    video_file = create_video(script["scenes"])

    print("✅ Video successfully ban gaya!")
    print(f"Title: {script['title']}")
    print("📁 final_video.mp4 ready hai")

    # Upload part abhi comment hai taaki error na aaye
    # upload_to_youtube(...)  
    print("Upload abhi band hai. Token issue fix hone ke baad on kar denge.")
