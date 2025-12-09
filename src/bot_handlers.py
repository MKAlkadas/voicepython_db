import os
import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.stt_service import STTService
from src.nlp_service import NLPProcessor
from src.pdf_service import PDFGenerator
from src.db_service import DBService

# Initialize services
# You might want to pass config here in a real app
db_service = DBService(db_path="products.db")
# Seed data for demonstration
db_service.seed_data()

stt_service = STTService(credentials_path="google_credentials.json")
nlp_processor = NLPProcessor(db_service=db_service)
pdf_generator = PDFGenerator(output_dir="temp")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً! أرسل لي رسالة صوتية بطلبك وسأقوم بإنشاء عرض سعر لك.\n"
        "Hello! Send me a voice message with your order and I will generate a quote."
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text("جاري معالجة طلبك... / Processing your request...")
    
    # 1. Download Voice File
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    file_path = os.path.join("temp", f"{voice_file.file_id}.oga")
    await voice_file.download_to_drive(file_path)
    
    # 2. Transcribe
    await update.message.reply_text("تحويل الصوت إلى نص... / Transcribing audio...")
    text = stt_service.transcribe_audio(file_path)
    await update.message.reply_text(f"النص المستخرج / Extracted Text:\n{text}")
    
    # 3. Extract Data
    data = nlp_processor.extract_data(text)
    data['customer_id'] = user.full_name
    
    # 4. Generate PDF
    await update.message.reply_text("إنشاء ملف PDF... / Generating PDF...")
    pdf_path = pdf_generator.generate_quote(data, filename=f"quote_{voice_file.file_id}.pdf")
    
    # 5. Send PDF
    await update.message.reply_document(document=open(pdf_path, 'rb'), filename="quote.pdf")
    
    # Cleanup (Optional)
    os.remove(file_path)
    os.remove(pdf_path)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Handle text messages same as voice for testing
    text = update.message.text
    await update.message.reply_text(f"معالجة النص... / Processing text...")
    
    data = nlp_processor.extract_data(text)
    data['customer_id'] = update.message.from_user.full_name
    
    pdf_path = pdf_generator.generate_quote(data, filename=f"quote_{update.message.message_id}.pdf")
    await update.message.reply_document(document=open(pdf_path, 'rb'), filename="quote.pdf")
