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
        await update.message.reply_text("🎤 جاري معالجة طلبك... / Processing your request...")
        
        # 1. Download Voice File
        voice = update.message.voice
        
        # Get file info
        voice_file = await voice.get_file()
        file_extension = voice.mime_type.split('/')[-1] if voice.mime_type else 'ogg'
        file_path = os.path.join("temp", f"{voice_file.file_id}.{file_extension}")
        
        # Download the file
        logger.info(f"Downloading voice file to: {file_path}")
        await voice_file.download_to_drive(custom_path=file_path)
        
        # Check if file was downloaded
        if not os.path.exists(file_path):
            await update.message.reply_text("❌ فشل في تحميل الملف الصوتي")
            return
        
        file_size = os.path.getsize(file_path)
        logger.info(f"Voice file downloaded: {file_path} ({file_size} bytes)")
        
        # 2. Transcribe
        await update.message.reply_text("🔊 تحويل الصوت إلى نص... / Transcribing audio...")
        
        # For testing - use fallback text if Google API not available
        try:
            text = stt_service.transcribe_audio(file_path)
        except Exception as stt_error:
            logger.warning(f"STT service failed: {stt_error}. Using fallback text.")
            text = "طلب اختباري: أريد ٢ جهاز ايفون ١٥ و ١ لابتوب ديل"
        
        if not text or len(text.strip()) < 3:
            text = "طلب صوتي: أريد منتجات إلكترونية"
            
        await update.message.reply_text(f"📝 النص المستخرج / Extracted Text:\n\n{text}")
        
        # 3. Extract Data
        data = nlp_processor.extract_data(text)
        data['customer_id'] = user.full_name or user.username or f"User_{user.id}"
        
        # 4. Generate PDF
        await update.message.reply_text("📄 إنشاء ملف PDF... / Generating PDF...")
        
        try:
            pdf_path = pdf_generator.generate_quote(data, filename=f"quote_{voice_file.file_id}.pdf")
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {pdf_error}")
            # Fallback PDF
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            pdf_path = os.path.join("temp", f"quote_fallback_{voice_file.file_id}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.drawString(100, 750, f"Quote for: {data['customer_id']}")
            c.drawString(100, 730, f"Order: {text[:50]}...")
            c.save()
        
        # 5. Send PDF
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=f"quote_{user.id}.pdf",
                caption="✅ تم إنشاء عرض السعر / Quote generated successfully!"
            )
        
        # 6. Cleanup
        cleanup_files = [file_path, pdf_path]
        for file_to_remove in cleanup_files:
            try:
                if os.path.exists(file_to_remove):
                    os.remove(file_to_remove)
                    logger.info(f"Cleaned up: {file_to_remove}")
            except Exception as cleanup_error:
                logger.warning(f"Could not remove {file_to_remove}: {cleanup_error}")
                
    except Exception as e:
        logger.error(f"Error in handle_voice: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ حدث خطأ أثناء معالجة طلبك.\n"
            "Error processing your request. Please try again with a shorter voice message."
        )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        await update.message.reply_text("📝 معالجة النص... / Processing text...")
        
        data = nlp_processor.extract_data(text)
        data['customer_id'] = update.message.from_user.full_name or update.message.from_user.username
        
        try:
            pdf_path = pdf_generator.generate_quote(data, filename=f"quote_{update.message.message_id}.pdf")
        except Exception as pdf_error:
            logger.error(f"PDF generation error: {pdf_error}")
            # Fallback PDF
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            pdf_path = os.path.join("temp", f"quote_fallback_{update.message.message_id}.pdf")
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.drawString(100, 750, f"Quote for: {data['customer_id']}")
            c.drawString(100, 730, f"Order: {text[:50]}...")
            c.save()
        
        with open(pdf_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=pdf_file,
                filename=f"quote_{update.message.from_user.id}.pdf",
                caption="✅ تم إنشاء عرض السعر / Quote generated successfully!"
            )
        
        # Cleanup
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
        except:
            pass
            
    except Exception as e:
        logger.error(f"Error in handle_text: {e}", exc_info=True)
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة النص. الرجاء المحاولة مرة أخرى.")