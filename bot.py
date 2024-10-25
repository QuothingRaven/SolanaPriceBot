# Imports
import asyncio
import logging
import signal
import sys
import discord
import httpx
import io
import matplotlib.pyplot as plt
import datetime
from discord.ext import commands, tasks

# Configuration
TOKEN = 'YOUR TOKEN ID'  # ADD YOUR DISCORD TOKEN HERE
SOLANA_PRICE_URL = 'https://api.coingecko.com/api/v3/coins/solana'  # Update to Solana API
SOLANA_HISTORY_URL = "https://api.coingecko.com/api/v3/coins/solana/market_chart?vs_currency=usd&days=30"  # Update to Solana API
THUMBNAIL_URL = 'https://cryptologos.cc/logos/solana-sol-logo.png'  # Update to Solana logo
AUTHOR_URL = 'https://cryptologos.cc/logos/solana-sol-logo.png'  # Update to Solana logo
WEBSITE_LINK = 'https://solana.com/'  # Update to Solana website
UPDATE_INTERVAL = 1800  # Update every 30 minutes
EMBED_CHANNEL_ID = 'YOUR CHANNEL ID TO EMBED INTO'

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Bot Initialization
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="~", intents=intents)

# Cog Definition
class SolanaBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = httpx.AsyncClient()
        self.message_id = None
        self.update_statistics.start()

    def cog_unload(self):
        self.update_statistics.cancel()
        asyncio.create_task(self.client.aclose())

    # Data Fetching Methods
    async def fetch_solana_data(self):
        try:
            response = await self.client.get(SOLANA_PRICE_URL)
            response.raise_for_status()
            data = response.json()
            return data['market_data'] if 'market_data' in data else None
        except Exception as e:
            logger.error(f"Error fetching Solana data: {e}")
            return None

    async def fetch_price_history(self):
        try:
            response = await self.client.get(SOLANA_HISTORY_URL)
            response.raise_for_status()
            data = response.json()
            return data['prices'] if 'prices' in data else None
        except Exception as e:
            logger.error(f"Error fetching Solana price history: {e}")
            return None

    # Chart Generation
    def generate_chart(self, price_history):
        dates = [datetime.datetime.fromtimestamp(price[0] / 1000) for price in price_history]
        prices = [price[1] for price in price_history]

        plt.figure(figsize=(10, 6))
        plt.plot(dates, prices, color='blue')
        plt.title('Solana Price Last 30 Days')
        plt.xlabel('Date')
        plt.ylabel('Price (USD)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf

    # Embed Handling
    async def send_or_edit_embed(self, embed, chart_buffer=None):
        channel = self.bot.get_channel(EMBED_CHANNEL_ID)
        if not channel:
            logger.error(f"Channel ID {EMBED_CHANNEL_ID} not found.")
            return

        files = [discord.File(chart_buffer, filename="solana_chart.png")] if chart_buffer else []

        if self.message_id:
            try:
                message = await channel.fetch_message(self.message_id)
                await message.edit(embed=embed, attachments=files)
            except discord.NotFound:
                logger.warning("Message not found, creating a new one")
                message = await channel.send(files=files, embed=embed)
                self.message_id = message.id
        else:
            message = await channel.send(files=files, embed=embed)
            self.message_id = message.id

    # Main Update Task
    @tasks.loop(seconds=UPDATE_INTERVAL)
    async def update_statistics(self):
        try:
            solana_data = await self.fetch_solana_data()
            if not solana_data:
                return

            price = solana_data['current_price']['usd']
            change_24h = solana_data['price_change_percentage_24h']
            change_7d = solana_data['price_change_percentage_7d']
            change_30d = solana_data['price_change_percentage_30d']
            volume = solana_data['total_volume']['usd']
            mcap = solana_data['market_cap']['usd']
            supply = solana_data['circulating_supply']
            ath = solana_data['ath']['usd']
            ath_change_percentage = solana_data['ath_change_percentage']['usd']
            ath_date = solana_data['ath_date']['usd']
            block_time = solana_data.get('block_time_in_minutes', 'N/A')  # Update if necessary

            price_history = await self.fetch_price_history()
            chart_buffer = self.generate_chart(price_history) if price_history else None

            now = datetime.datetime.now()
            embed = discord.Embed(
                title='Solana Price & Statistics',
                description='Latest market data for Solana.',
                colour=discord.Colour.green()  # Change color if desired
            )
            embed.set_thumbnail(url=THUMBNAIL_URL)
            embed.set_author(name='', icon_url=THUMBNAIL_URL)
            if chart_buffer:
                embed.set_image(url="attachment://solana_chart.png")
            embed.add_field(name='Price', value=f'${price:,.5f}')
            embed.add_field(name='24 Hour Change', value=f'{change_24h:,.2f}%')
            embed.add_field(name='7 Day Change', value=f'{change_7d:,.2f}%')
            embed.add_field(name='30 Day Change', value=f'{change_30d:,.2f}%')
            embed.add_field(name='24 Hour Volume', value=f'${volume:,.0f}')
            embed.add_field(name='Market Cap', value=f'${mcap:,.0f}')
            embed.add_field(name='Circulating Supply', value=f'{supply:,.0f} SOL')
            embed.add_field(name='Block Time (minutes)', value=f'{block_time}')
            embed.add_field(name='All-Time High', value=f'${ath:,.5f}')
            embed.add_field(name='ATH Change %', value=f'{ath_change_percentage:,.2f}%')
            embed.add_field(name='ATH Date', value=datetime.datetime.fromisoformat(ath_date.replace('Z', '+00:00')).strftime('%Y-%m-%d'))
            embed.add_field(name='Links', value=f'[Website]({WEBSITE_LINK}) | [Explorer](https://explorer.solana.com/) | [Docs](https://docs.solana.com/)', inline=False)
            embed.add_field(name='Source', value='[Coingecko](https://www.coingecko.com/en/coins/solana)')
            embed.set_footer(text=f'Last updated on {now.strftime("%B %d, %Y at %H:%M")}', icon_url=AUTHOR_URL)

            await self.send_or_edit_embed(embed, chart_buffer)

        except Exception as e:
            logger.error(f"Error in update_statistics: {e}")

    @update_statistics.before_loop
    async def before_update_statistics(self):
        await self.bot.wait_until_ready()

    # Commands
    @commands.command(name="price")
    async def price(self, ctx):
        solana_data = await self.fetch_solana_data()
        if solana_data:
            price = solana_data['current_price']['usd']
            await ctx.send(f'Solana price is ${price:.5f} USD')
        else:
            await ctx.send('Failed to fetch Solana price.')

# Event Handlers
@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    logger.info('Bot is ready.')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Type ~help for available commands.")
    else:
        logger.error(f"An error occurred: {error}")
        await ctx.send("An error occurred while processing your command.")

# Utility Functions
def signal_handler(signum, frame):
    logger.info(f"Received shutdown signal: {signum}")
    sys.exit(0)

# Registering Signals for Graceful Shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Bot Setup and Main Execution
async def setup(bot):
    await bot.add_cog(SolanaBot(bot))

async def main():
    async with bot:
        await setup(bot)
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
