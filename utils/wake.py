import pvporcupine
import pyaudio
import struct
import os
from dotenv import load_dotenv

load_dotenv()

def listen_for_wake_word():
    print("🎙️ Listening for custom wake word...")

    access_key = os.getenv("PICOVOICE_KEY")
    keyword_path = os.path.join("assets", "wake_word", "hey-buddy.ppn")

    if not os.path.exists(keyword_path):
        print(f"❌ Wake word file not found at: {keyword_path}")
        return False

    porcupine = pvporcupine.create(
        access_key=access_key,
        keyword_paths=[keyword_path]  
    )

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=porcupine.sample_rate,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    try:
        while True:
            audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, audio_data)

            result = porcupine.process(pcm)
            if result >= 0:
                print("👂 Wake word detected!")
                return True
    except KeyboardInterrupt:
        print("👋 Wake word detection stopped manually.")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()
