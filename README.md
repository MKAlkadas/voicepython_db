# Voice-to-Quote Telegram Bot System

This system allows users to send voice messages to a Telegram bot, which then converts the speech to text, extracts product information, and generates a PDF price quote.

## Components

1.  **Telegram Bot**: Handles user interaction (Voice/Text).
2.  **STT Service**: Google Cloud Speech-to-Text (with mock fallback).
3.  **NLP Processor**: Extracts product, quantity, and specs from text.
4.  **PDF Generator**: Creates a professional PDF quote using ReportLab.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Install FFMPEG**:
    *   Required for converting Telegram audio (OGG) to WAV for Google Speech API.
    *   Download from [ffmpeg.org](https://ffmpeg.org/) and add to your system PATH.
    *   *Note: If you don't install FFMPEG, the bot will fail to convert audio.*

3.  **Configuration**:
    *   Rename `.env.example` to `.env`.
    *   Add your **Telegram Bot Token** (get it from @BotFather).
    *   (Optional) Add path to your **Google Cloud Credentials JSON** for real Speech-to-Text. If left empty, the system uses a Mock STT for testing.

4.  **Run the Bot**:
    ```bash
    python main.py
    ```

## Usage

1.  Start the bot with `/start`.
2.  Send a voice message saying something like:
    > "I want 5 pieces of iPhone 15 Pro Max"
    > OR
    > "اريد 5 قطع من ايفون 15 برو ماكس"
3.  The bot will reply with the extracted text and a PDF file containing the quote.
