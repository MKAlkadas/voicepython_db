import os
import subprocess
import tempfile
from google.cloud import speech_v1 as speech

class STTService:
    def __init__(self, credentials_path=None):
        """Initialize Google Speech-to-Text service"""
        self.client = None
        # Note: Google Cloud credentials should be set via environment variable
        # GOOGLE_APPLICATION_CREDENTIALS in Render dashboard
        
    def _get_client(self):
        """Lazy initialization of speech client"""
        if self.client is None:
            self.client = speech.SpeechClient()
        return self.client
    
    def convert_audio_to_wav(self, input_path):
        """
        Convert any audio format to WAV using ffmpeg
        Returns path to converted WAV file
        """
        try:
            # Create a temporary WAV file
            temp_wav = tempfile.mktemp(suffix='.wav')
            
            # Use ffmpeg to convert
            cmd = [
                'ffmpeg',
                '-i', input_path,      # Input file
                '-acodec', 'pcm_s16le', # Audio codec
                '-ar', '16000',        # Sample rate
                '-ac', '1',            # Mono channel
                '-y',                  # Overwrite output
                temp_wav
            ]
            
            # Run ffmpeg
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                print(f"FFmpeg error: {process.stderr}")
                return None
            
            if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 0:
                return temp_wav
            else:
                return None
                
        except Exception as e:
            print(f"Audio conversion error: {e}")
            return None
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe audio file to text using Google Speech-to-Text
        """
        client = self._get_client()
        
        # Convert to WAV if needed
        if not audio_path.endswith('.wav'):
            wav_path = self.convert_audio_to_wav(audio_path)
            if wav_path:
                audio_path = wav_path
                is_temp_file = True
            else:
                return "فشل في تحويل الملف الصوتي"
        else:
            is_temp_file = False
        
        try:
            # Read audio file
            with open(audio_path, 'rb') as audio_file:
                content = audio_file.read()
            
            # Configure recognition
            audio = speech.RecognitionAudio(content=content)
            
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code="ar-SA",  # Arabic - Saudi Arabia
                enable_automatic_punctuation=True,
                model="latest_long"  # Better for longer audio
            )
            
            # Perform transcription
            response = client.recognize(config=config, audio=audio)
            
            # Combine results
            transcript_parts = []
            for result in response.results:
                transcript_parts.append(result.alternatives[0].transcript)
            
            transcript = " ".join(transcript_parts)
            
            # Cleanup temporary file
            if is_temp_file:
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            return transcript.strip() if transcript else "لم أتمكن من التعرف على الكلام"
            
        except Exception as e:
            print(f"Speech recognition error: {e}")
            # Fallback: return a placeholder text for testing
            return f"طلب اختباري: {os.path.basename(audio_path)}"
    
    # Alias for compatibility
    def transcribe_audio_file(self, file_path):
        return self.transcribe_audio(file_path)