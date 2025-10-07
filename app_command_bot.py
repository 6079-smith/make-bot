import discord
from discord import app_commands
import os
import aiohttp
import json
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID_STR = os.getenv("DISCORD_GUILD_ID")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
MAKE_HEADER_NAME = os.getenv("MAKE_HEADER_NAME")
MAKE_HEADER_VALUE = os.getenv("MAKE_HEADER_VALUE")
QUERY_CHANNEL_ID_STR = os.getenv("DISCORD_QUERY_CHANNEL_ID")

# --- Validation ---
if not all([BOT_TOKEN, GUILD_ID_STR, MAKE_WEBHOOK_URL, QUERY_CHANNEL_ID_STR]):
    raise ValueError("A required environment variable is missing.")
try:
    GUILD_ID = discord.Object(id=int(GUILD_ID_STR))
except ValueError:
    raise ValueError("DISCORD_GUILD_ID must be a valid integer.")
try:
    QUERY_CHANNEL_ID = int(QUERY_CHANNEL_ID_STR)
except ValueError:
    raise ValueError("DISCORD_QUERY_CHANNEL_ID must be a valid integer.")

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(
    name="query",
    description="Submit a query to the customer service AI.",
    guild=GUILD_ID
)
@app_commands.describe(prompt="Your question, e.g., 'where is my order: #STG1063'")
async def query_command(interaction: discord.Interaction, prompt: str):
    await interaction.response.defer(ephemeral=True)

    payload = {"message": prompt}
    # Base headers
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    # Optional auth/custom header
    if MAKE_HEADER_VALUE:
        if MAKE_HEADER_NAME:
            headers[MAKE_HEADER_NAME] = MAKE_HEADER_VALUE
        else:
            # Fallback to Authorization header if only a value is provided
            headers["Authorization"] = MAKE_HEADER_VALUE

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MAKE_WEBHOOK_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    await interaction.followup.send("Your query has been sent for processing.", ephemeral=True)
                else:
                    print(f"Error forwarding to Make.com. Status: {response.status}, Response: {await response.text()}")
                    await interaction.followup.send(f"An error occurred while processing your request. Status: {response.status}", ephemeral=True)
        except aiohttp.ClientError as e:
            print(f"An HTTP client error occurred: {e}")
            await interaction.followup.send("A network error occurred. Please try again later.", ephemeral=True)

@client.event
async def on_message(message: discord.Message):
    # Ignore messages from bots (including itself)
    if message.author.bot:
        return

    # Only handle messages from the designated query channel
    if message.channel.id != QUERY_CHANNEL_ID:
        return

    content = message.content.strip()
    if not content:
        return

    # Ignore messages that look like commands (let other bots work)
    IGNORE_PREFIXES = ("/", "!", "?", ".")
    if content.startswith(IGNORE_PREFIXES):
        return

    payload = {
        "message": content,
        "author": {
            "id": str(message.author.id),
            "username": str(message.author),
            "display_name": getattr(message.author, "display_name", None),
        },
        "message_url": message.jump_url,
        "message_id": str(message.id),
        "channel_id": str(message.channel.id),
        "channel_name": getattr(message.channel, "name", None),
        "guild_id": str(message.guild.id) if message.guild else None,
        "guild_name": message.guild.name if message.guild else None,
        "created_at": message.created_at.isoformat(),
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if MAKE_HEADER_VALUE:
        if MAKE_HEADER_NAME:
            headers[MAKE_HEADER_NAME] = MAKE_HEADER_VALUE
        else:
            headers["Authorization"] = MAKE_HEADER_VALUE

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MAKE_WEBHOOK_URL, json=payload, headers=headers) as response:
                if response.status == 200:
                    pass
                else:
                    text = await response.text()
                    print(f"Error forwarding to Make.com. Status: {response.status}, Response: {text}")
                    pass
    except aiohttp.ClientError as e:
        print(f"An HTTP client error occurred: {e}")
        pass

@client.event
async def on_ready():
    await tree.sync(guild=GUILD_ID)
    print(f'Logged in as {client.user}')
    print('Application commands synced. Bot is ready.')

# --- Run Bot ---
client.run(BOT_TOKEN)