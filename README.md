# Solana Discord Bot

This Discord bot provides real-time price and market statistics for Solana. It fetches data from the CoinGecko API and updates a designated Discord channel with the latest information, including price charts.

## Features

- Fetches current price and market statistics for Solana.
- Generates and embeds price charts for the last 30 days.
- Updates the information every 30 minutes.
- Responds to user commands to fetch the current price.

## Requirements

- Python 3.7 or higher
- Discord bot token
- Access to a Discord server

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd solana-discord-bot
2. Create a virtual environment (optional but recommended):

bash
Copy code
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

3. Install the required packages:

bash
Copy code
pip install -r requirements.txt

4. Update the configuration section in the code:

Replace YOUR TOKEN ID with your Discord bot token.
Replace YOUR CHANNEL ID TO EMBED INTO with the ID of the channel where you want the bot to send messages.

5. Run the bot:

bash
Copy code
python bot.py

## Usage
Use the command ~price in Discord to get the current price of Solana.
The bot will automatically update its statistics every 30 minutes in the specified channel.
