import speech_recognition as sr

def listen_and_transcribe(language="en-US", retries=10):
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    for _ in range(retries):
        with mic as source:
            print(f"🎤 Listening for command in {language}...")

            recognizer.adjust_for_ambient_noise(source, duration=1)  # 🧠 Use background noise calibration

            try:
                audio = recognizer.listen(
                    source,
                    timeout=5,           # Wait max 5s for speech to start
                    phrase_time_limit=15  # Allow up to 15s of speech
                )
                print(f"📝 Transcribing speech in {language}...")
                text = recognizer.recognize_google(audio, language=language)
                print(f"📝 Transcribed: {text}")
                return text
            except sr.WaitTimeoutError:
                print("⏱️ Timeout: No speech detected.")
            except sr.UnknownValueError:
                print("🔊 Sorry, I couldn't understand that.")
            except sr.RequestError:
                print("⚠️ API request error.")
            except Exception as e:
                print(f"⚠️ Unexpected error: {e}")

    return None
