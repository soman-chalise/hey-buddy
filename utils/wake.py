import pvporcupine
import pyaudio
import struct
import os
from dotenv import load_dotenv

load_dotenv()

import speech_recognition as sr

def listen_for_wake_word():
    print("🎙️ Listening for wake phrase: 'hey buddy'")

    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("📢 Adjusted for ambient noise. Ready...")

        while True:
            try:
                print("🎧 Listening...")
                audio = recognizer.listen(source, phrase_time_limit=30000)
                text = recognizer.recognize_google(audio).lower()
                print(f"🗣️ Heard: {text}")

                if "hey buddy" in text:
                    print("👂 Wake phrase detected!")
                    return True
            except sr.UnknownValueError:
                # Didn't understand audio
                pass
            except sr.RequestError as e:
                print(f"❌ Could not request results; {e}")
                break

