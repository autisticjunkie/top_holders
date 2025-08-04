import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode
from dotenv import load_dotenv
from alchemy_client import AlchemyClient

# Load environment variables
load_dotenv()

# Simple health check handler for Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TokenHolderBot:
    def __init__(self):
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.alchemy_api_key = os.getenv("ALCHEMY_API_KEY")
        self.authorized_user_id = os.getenv("AUTHORIZED_USER_ID")
        
        if not self.telegram_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        if not self.alchemy_api_key:
            raise ValueError("ALCHEMY_API_KEY not found in environment variables")
        if not self.authorized_user_id:
            raise ValueError("AUTHORIZED_USER_ID not found in environment variables")
        
        try:
            self.authorized_user_id = int(self.authorized_user_id)
        except ValueError:
            raise ValueError("AUTHORIZED_USER_ID must be a valid integer")
        
        self.alchemy_client = AlchemyClient(self.alchemy_api_key)
        self.application = Application.builder().token(self.telegram_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("th", self.top_holders_command))
        self.application.add_handler(CommandHandler("whoami", self.whoami_command))
    
    def is_authorized_user(self, user_id: int) -> bool:
        """Check if user is authorized to use the bot"""
        return user_id == self.authorized_user_id
    
    async def send_unauthorized_message(self, update: Update):
        """Send unauthorized access message"""
        await update.message.reply_text(
            "🚫 **Access Denied**\n\n"
            "This bot is private and only available to authorized users.\n\n"
            f"Your User ID: `{update.effective_user.id}`\n\n"
            "If you believe this is an error, please contact the bot owner.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        if not self.is_authorized_user(update.effective_user.id):
            await self.send_unauthorized_message(update)
            return
            
        welcome_message = """
🤖 **Token Holder Analysis Bot**

Welcome! I can analyze the top holders of any token on Abstract Chain.

**Commands:**
• `/th <token_address>` - Get top 20 holders of a token
• `/help` - Show this help message
• `/whoami` - Show your user information

**Example:**
`/th 0x1234567890123456789012345678901234567890`

I'll show you each holder's balance and their other significant token holdings!
        """
        await update.message.reply_text(welcome_message, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        if not self.is_authorized_user(update.effective_user.id):
            await self.send_unauthorized_message(update)
            return
            
        help_message = """
🔍 **How to use this bot:**

**Command:** `/th <token_address>`

**What I'll show you:**
• Top 20 holders by balance
• Each holder's token balance
• Their top 5 other token holdings (up to 10 total)
• Addresses are shortened for readability

**Example:**
`/th 0x1234567890123456789012345678901234567890`

**Note:** Analysis is performed on Abstract Chain (Chain ID: 2741)

**Tips:**
• Make sure the token address is valid (42 characters, starts with 0x)
• Analysis may take 10-30 seconds for tokens with many transfers
• I'll show a warning if the analysis takes too long
        """
        await update.message.reply_text(help_message, parse_mode=ParseMode.MARKDOWN)
    
    async def whoami_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /whoami command to show user info"""
        user = update.effective_user
        is_authorized = self.is_authorized_user(user.id)
        
        status = "✅ **Authorized**" if is_authorized else "❌ **Not Authorized**"
        
        info_message = f"""
👤 **User Information**

**Name:** {user.first_name} {user.last_name or ''}
**Username:** @{user.username or 'N/A'}
**User ID:** `{user.id}`
**Status:** {status}

**Bot Access:** {'Granted' if is_authorized else 'Denied'}
        """
        
        await update.message.reply_text(info_message, parse_mode=ParseMode.MARKDOWN)
    
    async def top_holders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /th command to analyze top holders"""
        if not self.is_authorized_user(update.effective_user.id):
            await self.send_unauthorized_message(update)
            return
            
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide a token address.\n\n"
                "**Usage:** `/th <token_address>`\n"
                "**Example:** `/th 0x1234567890123456789012345678901234567890`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        token_address = context.args[0].strip()
        
        # Validate token address format
        if not self.is_valid_address(token_address):
            await update.message.reply_text(
                "❌ Invalid token address format.\n\n"
                "Please provide a valid Ethereum address (42 characters, starting with 0x)",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Send initial processing message
        processing_msg = await update.message.reply_text(
            "🔍 Analyzing token holders...\n"
            "This may take 10-30 seconds depending on transfer volume.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Get token metadata first
            token_metadata = await self.get_token_info(token_address)
            
            # Get top holders
            top_holders = self.alchemy_client.get_top_holders(token_address, top_n=20)
            
            if not top_holders:
                await processing_msg.edit_text(
                    "❌ No holders found for this token.\n\n"
                    "This could mean:\n"
                    "• Token address is incorrect\n"
                    "• Token has no transfers yet\n"
                    "• Token is not on Abstract Chain",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            # Format the response
            response = await self.format_holders_response(
                token_address, token_metadata, top_holders
            )
            
            # Edit the processing message with results
            await processing_msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            error_message = f"❌ **Error analyzing token:**\n\n`{str(e)}`\n\n"
            error_message += "**Possible causes:**\n"
            error_message += "• Invalid token address\n"
            error_message += "• Token not on Abstract Chain\n"
            error_message += "• API rate limit reached\n"
            error_message += "• Network connectivity issues"
            
            await processing_msg.edit_text(error_message, parse_mode=ParseMode.MARKDOWN)
            logger.error(f"Error in top_holders_command: {e}")
    
    def is_valid_address(self, address: str) -> bool:
        """Validate Ethereum address format"""
        if not address or not isinstance(address, str):
            return False
        
        # Remove 0x prefix if present
        if address.startswith("0x"):
            address = address[2:]
        
        # Check if it's 40 hex characters
        if len(address) != 40:
            return False
        
        try:
            int(address, 16)
            return True
        except ValueError:
            return False
    
    async def get_token_info(self, token_address: str) -> dict:
        """Get token metadata"""
        try:
            return self.alchemy_client.get_token_metadata(token_address)
        except Exception as e:
            logger.warning(f"Could not fetch token metadata: {e}")
            return {"symbol": "UNKNOWN", "name": "Unknown Token", "decimals": 18}
    
    async def format_holders_response(self, token_address: str, token_metadata: dict, top_holders: list) -> str:
        """Format the top holders response message"""
        symbol = token_metadata.get("symbol", "UNKNOWN")
        name = token_metadata.get("name", "Unknown Token")
        decimals = token_metadata.get("decimals", 18)
        
        response = f"🏆 **Top {len(top_holders)} Holders of {symbol}**\n"
        response += f"*{name}*\n"
        response += f"📍 Contract: [{self.alchemy_client.shorten_address(token_address)}](https://abscan.org/address/{token_address})\n\n"
        
        for i, (holder_address, balance) in enumerate(top_holders, 1):
            formatted_balance = self.alchemy_client.format_balance(balance, decimals)
            short_address = self.alchemy_client.shorten_address(holder_address)
            
            response += f"**#{i}** [{short_address}](https://abscan.org/address/{holder_address})\n"
            response += f"💰 **{formatted_balance} {symbol}**\n"
            
            # Other holdings feature removed for cleaner output
            
            response += "\n"
        

        
        return response
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Token Holder Analysis Bot...")
        
        # Check if running on Render (has PORT env var)
        port = os.getenv('PORT')
        
        if port:
            # Start HTTP health check server for Render
            logger.info(f"Starting health check server on port {port}")
            server = HTTPServer(('0.0.0.0', int(port)), HealthCheckHandler)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            logger.info(f"Health check server running on port {port}")
            
            # Use polling for bot (more reliable)
            logger.info("Starting bot in polling mode")
            self._run_polling()
        else:
            # Use polling for local development
            logger.info("Using polling mode for local development")
            self._run_polling()
    
    def _run_polling(self):
        """Fallback polling mode"""
        try:
            self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
        except Exception as e:
            logger.error(f"Bot failed to start: {e}")
            raise

def main():
    """Main function to run the bot"""
    try:
        bot = TokenHolderBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
