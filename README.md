# Token Holder Analysis Bot

A Telegram bot that analyzes the top holders of any ERC-20 token on Abstract Chain using the Alchemy API.

## Features

- 🔍 **Top Holder Analysis**: Get the top 20 holders of any token
- 💰 **Balance Information**: Shows each holder's token balance in human-readable format
- 🔗 **Clickable Links**: Wallet addresses link directly to Abstract Chain explorer
- 📱 **Telegram Integration**: Easy-to-use Telegram bot interface
- ⚡ **Real-time Data**: Uses Alchemy API for accurate, up-to-date information
- 🚀 **Fast Performance**: Optimized for quick responses (~20 seconds)

## How It Works

1. **Transfer Analysis**: Fetches all ERC-20 transfers for the specified token using `alchemy_getAssetTransfers`
2. **Balance Reconstruction**: Simulates block explorer behavior by aggregating transfers to calculate current balances
3. **Top Holder Identification**: Sorts addresses by balance and identifies the top 20 holders
4. **Balance Verification**: Uses `eth_call` with `balanceOf()` to verify current token balances
5. **Metadata Enhancement**: Uses `alchemy_getTokenMetadata` to convert raw balances to human-readable format

## Setup

### Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Alchemy API Key with Abstract Chain access

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /path/to/Top_Holders
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your credentials:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   ALCHEMY_API_KEY=your_alchemy_api_key_here
   ```

### Getting API Keys

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command and follow instructions
3. Copy the bot token provided

#### Alchemy API Key
1. Sign up at [Alchemy](https://www.alchemy.com/)
2. Create a new app with Abstract Chain network
3. Copy your API key from the dashboard

## Usage

### Running the Bot

```bash
python telegram_bot.py
```

### Bot Commands

- `/start` - Welcome message and basic instructions
- `/help` - Detailed help and usage examples
- `/th <token_address>` - Analyze top holders of a token

### Example Usage

```
/th 0x1234567890123456789012345678901234567890
```

The bot will respond with:
- Top 5 holders and their balances
- Each holder's 2-3 largest other token holdings
- Formatted addresses and human-readable amounts

## Technical Details

### Abstract Chain Configuration
- **Chain ID**: 2741
- **RPC URL**: `https://abstract-mainnet.g.alchemy.com/v2/<API_KEY>`

### API Methods Used
- `alchemy_getAssetTransfers` - Fetch all token transfers
- `alchemy_getTokenBalances` - Get holder's other token balances
- `alchemy_getTokenMetadata` - Get token symbol, name, and decimals

### Optimizations
- **Pagination**: Handles large transfer datasets with automatic pagination
- **Caching**: Balance calculations are optimized for performance
- **Error Handling**: Graceful handling of API errors and invalid inputs
- **Rate Limiting**: Built-in request management to avoid API limits

### Response Format
```
🏆 Top 5 Holders of TOKEN
Contract: 0xAbc...123

#1 0x123...abc
💰 1.25M TOKEN
🔸 Other holdings:
   • 500K USDC
   • 1.2K ETH

#2 0x456...def
💰 800K TOKEN
🔸 Other holdings:
   • 2.1M DAI
   • 50 WETH
```

## Error Handling

The bot handles various error scenarios:
- Invalid token addresses
- Tokens with no transfers
- API rate limits
- Network connectivity issues
- Malformed responses

## Security Notes

- API keys are loaded from environment variables
- No sensitive data is logged
- Input validation prevents malicious addresses
- Graceful error messages don't expose internal details

## Deployment

### Deploy to Render (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy token holder bot"
   git push origin main
   ```

2. **Deploy on Render**:
   - Go to [render.com](https://render.com) and sign up/login
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the `render.yaml` configuration
   - Set environment variables:
     - `ALCHEMY_API_KEY`: Your Alchemy API key
     - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
     - `AUTHORIZED_USER_ID`: Your Telegram user ID
   - Click "Deploy"

3. **Alternative Manual Setup**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python telegram_bot.py`
   - Environment: Python 3

### Other Deployment Options

- **Heroku**: Use the included `requirements.txt`
- **Railway**: Auto-detects Python and requirements
- **DigitalOcean App Platform**: Works with the render.yaml config
- **VPS**: Run directly with `python telegram_bot.py`

## Limitations

- Analysis limited to Abstract Chain (Chain ID: 2741)
- Real-time balance verification with current token balances
- Maximum 10,000 transfers processed per analysis
- Rate limited by Alchemy API quotas

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.
