#!/usr/bin/env python3
"""
Simple script to help you get your Telegram User ID
Run this script and then message your bot to see your user ID
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message and return user info"""
    user = update.effective_user
    
    response = f"""
👤 **Your Telegram Information:**

**Name:** {user.first_name} {user.last_name or ''}
**Username:** @{user.username or 'N/A'}
**User ID:** `{user.id}`
**Language:** {user.language_code or 'N/A'}

📝 **To authorize this bot:**
1. Copy your User ID: `{user.id}`
2. Add it to your .env file as: `AUTHORIZED_USER_ID={user.id}`
3. Restart the bot

🔒 **This bot will only respond to User ID: {user.id}**
    """
    
    await update.message.reply_text(response)
    
    # Also log to console
    print(f"\n{'='*50}")
    print(f"📱 NEW USER MESSAGE RECEIVED")
    print(f"{'='*50}")
    print(f"Name: {user.first_name} {user.last_name or ''}")
    print(f"Username: @{user.username or 'N/A'}")
    print(f"User ID: {user.id}")
    print(f"Message: {update.message.text}")
    print(f"{'='*50}")
    print(f"🔧 Add this to your .env file:")
    print(f"AUTHORIZED_USER_ID={user.id}")
    print(f"{'='*50}\n")

def main():
    """Main function to run the user ID helper bot"""
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not telegram_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Please add your bot token to the .env file first")
        return
    
    print("🤖 Starting User ID Helper Bot...")
    print("📱 Send any message to your bot to get your User ID")
    print("🛑 Press Ctrl+C to stop")
    
    # Create application
    application = Application.builder().token(telegram_token).build()
    
    # Add message handler for all text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
