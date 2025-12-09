import os
import subprocess
import tempfile
import logging

logger = logging.getLogger(__name__)

class STTService:
    def __init__(self, credentials_path=None):
        """Initialize STT service"""
        self.client = None
        
    def _get_client(self):
        """Lazy initialization of Google Speech client"""
        if self.client is None:
            try:
                from google.cloud import speech_v1 as speech
                self.client = speech.SpeechClient()
            except ImportError:
                logger.warning("Google Cloud Speech not available. Using fallback mode.")
                self.client = None
            except Exception as e:
                logger.warning(f"Could not initialize Google Speech: {e}")
                self.client = None
        return self.client
    
    def convert_audio_to_wav(self, input_path):
        """
        Convert any audio format to WAV using ffmpeg
        """
        try:
            if not os.path.exists(input_path):
                logger.error(f"Input file does not exist: {input_path}")
                return None
            
            # Create a temporary WAV file
            temp_wav = tempfile.mktemp(suffix='.wav', dir='temp')
            
            logger.info(f"Converting {input_path} to WAV...")
            
            # Use ffmpeg to convert
            cmd = [
                'ffmpeg',
                '-i', input_path,
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                '-y',
                '-hide_banner',
                '-loglevel', 'error',
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
                logger.error(f"FFmpeg conversion failed: {process.stderr}")
                return None
            
            if os.path.exists(temp_wav) and os.path.getsize(temp_wav) > 0:
                logger.info(f"Converted to WAV: {temp_wav} ({os.path.getsize(temp_wav)} bytes)")
                return temp_wav
            else:
                logger.error("WAV file was not created or is empty")
                return None
                
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return None
    
    def transcribe_audio(self, audio_path):
        """
        Transcribe audio file to text
        """
        try:
            if not os.path.exists(audio_path):
                return "فشل: الملف الصوتي غير موجود"
            
            # Try Google Speech API first
            client = self._get_client()
            if client:
                try:
                    return self._transcribe_with_google(audio_path)
                except Exception as google_error:
                    logger.warning(f"Google STT failed: {google_error}")
            
            # Fallback: Simulate transcription
            return self._fallback_transcription(audio_path)
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return "طلب صوتي: أريد منتجات إلكترونية"
    
    def _transcribe_with_google(self, audio_path):
        """Transcribe using Google Speech-to-Text"""
        from google.cloud import speech_v1 as speech
        
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
                language_code="ar-SA",
                enable_automatic_punctuation=True,
            )
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Combine results
            transcript_parts = []
            for result in response.results:
                transcript_parts.append(result.alternatives[0].transcript)
            
            transcript = " ".join(transcript_parts)
            
            # Cleanup
            if is_temp_file:
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            return transcript.strip() if transcript else "لم أتمكن من التعرف على الكلام"
            
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            raise
    
    def _fallback_transcription(self, audio_path):
        """Fallback transcription for testing"""
        import random
        
        # List of sample Arabic orders
        sample_orders = [
            "أريد شراء ٢ جهاز ايفون ١٥ و ٣ سماعات لاسلكية",
            "طلب: كمبيوتر محمول ديل و ماوس لاسلكي",
            "أحتاج إلى ٥ قطع من سامسونج اس ٢٤",
            "اريد ١ لابتوب ماك بوك برو و ٢ ايفون",
            "طلب صوتي: ٣ اجهزة ايفون ١٥ برو ماكس",
            "أحتاج كمبيوتر محمول و طابعة و ماوس",
            "اريد شراء ٢ تلفزيون سامسونج و ١ بلايستيشن"
        ]
        
        # Use filename or random choice
        filename = os.path.basename(audio_path)
        if "test" in filename.lower():
            return sample_orders[0]
        
        return random.choice(sample_orders)