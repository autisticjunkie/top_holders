#!/usr/bin/env python3
"""
Simple script to clear Telegram bot webhook and pending updates
Run this if you're having conflicts between multiple bot instances
"""

import os
import asyncio
import logging
from telegram import Bot
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_webhook():
    """Clear webhook and pending updates"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
        return
    
    bot = Bot(token=token)
    
    try:
        # Delete webhook and drop pending updates
        result = await bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"Webhook cleared: {result}")
        
        # Get bot info to verify connection
        me = await bot.get_me()
        logger.info(f"Bot info: @{me.username} ({me.first_name})")
        
        logger.info("✅ Webhook cleared successfully! You can now start your bot.")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear webhook: {e}")
    
    finally:
        # Close the bot session
        await bot.close()

if __name__ == "__main__":
    asyncio.run(clear_webhook())
