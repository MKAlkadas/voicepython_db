import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from stt_service import STTService
from nlp_service import NLPProcessor
from pdf_service import PDFGenerator
from db_service import DBService

# Initialize services
db_service = DBService(db_path="products.db")
db_service.seed_data()

stt_service = STTService()
nlp_processor = NLPProcessor(db_service=db_service)
pdf_generator = PDFGenerator(output_dir="temp")

# Ensure temp directory exists
if not os.path.exists("temp"):
    os.makedirs("temp", exist_ok=True)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي رسالة صوتية بطلبك وسأقوم بإنشاء عرض سعر لك.\n"
        "Hello! Send me a voice message with your order and I will generate a quote."
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.from_user
        await update.message.reply_text("🎤 جاري معالجة طلبك...")
        
        # Download voice file
        voice_file = await update.message.voice.get_file()
        file_path = f"temp/{voice_file.file_id}.ogg"
        
        await voice_file.download_to_drive(custom_path=file_path)
        
        # Transcribe
        await update.message.reply_text("🔊 تحويل الصوت إلى نص...")
        text = stt_service.transcribe_audio(file_path) or "طلب صوتي"
        
        await update.message.reply_text(f"📝 النص: {text}")
        
        # Extract data
        data = nlp_processor.extract_data(text)
        data['customer_id'] = user.full_name or user.username
        
        # Generate PDF
        await update.message.reply_text("📄 إنشاء ملف PDF...")
        pdf_path = pdf_generator.generate_quote(data, filename=f"quote_{voice_file.file_id}.pdf")
        
        # Send PDF
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename="quote.pdf",
                caption="✅ تم إنشاء عرض السعر"
            )
        
        # Cleanup
        for f in [file_path, pdf_path]:
            try:
                os.remove(f)
            except:
                pass
                
    except Exception as e:
        logger.error(f"Error in handle_voice: {e}")
        await update.message.reply_text("❌ حدث خطأ. حاول مرة أخرى.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        await update.message.reply_text("📝 معالجة النص...")
        
        data = nlp_processor.extract_data(text)
        data['customer_id'] = update.message.from_user.full_name or update.message.from_user.username
        
        pdf_path = pdf_generator.generate_quote(data, filename=f"quote_{update.message.message_id}.pdf")
        
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename="quote.pdf",
                caption="✅ تم إنشاء عرض السعر"
            )
        
        # Cleanup
        try:
            os.remove(pdf_path)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error in handle_text: {e}")
        await update.message.reply_text("❌ حدث خطأ. حاول مرة أخرى.")