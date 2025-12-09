import os
from google.cloud import speech
import io
from pydub import AudioSegment

class STTService:
    def __init__(self, credentials_path=None):
        self.credentials_path = credentials_path
        # If credentials are provided, initialize the client
        if credentials_path and os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            self.client = speech.SpeechClient()
        else:
            self.client = None
            print("Warning: Google Cloud credentials not found. STT will run in MOCK mode.")

        # Configure FFMPEG using imageio-ffmpeg
        try:
            import imageio_ffmpeg
            AudioSegment.converter = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            print("Warning: imageio-ffmpeg not installed. Audio conversion might fail.")

    def convert_ogg_to_wav(self, ogg_path):
        """
        Converts OGG audio to WAV format using pydub (requires ffmpeg).
        """
        try:
            audio = AudioSegment.from_file(ogg_path, format="ogg")
            wav_path = ogg_path.replace(".ogg", ".wav").replace(".oga", ".wav")
            audio.export(wav_path, format="wav")
            return wav_path
        except Exception as e:
            print(f"Error converting audio: {e}")
            print("Make sure FFMPEG is installed and added to PATH.")
            return None

    def transcribe_audio(self, audio_path, language_code="ar-SA"):
        """
        Transcribes audio file to text.
        """
        if not self.client:
            return self.mock_transcribe(audio_path)

        # Convert if necessary
        if audio_path.endswith(".ogg") or audio_path.endswith(".oga"):
            wav_path = self.convert_ogg_to_wav(audio_path)
            if not wav_path:
                return "Error: Could not convert audio file."
            audio_path = wav_path

        try:
            with io.open(audio_path, "rb") as audio_file:
                content = audio_file.read()

            audio = speech.RecognitionAudio(content=content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                # sample_rate_hertz=16000, # Let it detect automatically or set if known
                language_code=language_code,
            )

            response = self.client.recognize(config=config, audio=audio)

            # Concatenate results
            transcript = ""
            for result in response.results:
                transcript += result.alternatives[0].transcript + " "
            
            return transcript.strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return f"Error during transcription: {str(e)}"

    def mock_transcribe(self, audio_path):
        """
        Mock transcription for testing without API keys.
        """
        print(f"Mock transcribing file: {audio_path}")
        return "اريد 5 قطع من لابتوب ديل اكس بي اس"
