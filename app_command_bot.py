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

# --- Validation ---
if not all([BOT_TOKEN, GUILD_ID_STR, MAKE_WEBHOOK_URL]):
    raise ValueError("A required environment variable is missing.")
try:
    GUILD_ID = discord.Object(id=int(GUILD_ID_STR))
except ValueError:
    raise ValueError("DISCORD_GUILD_ID must be a valid integer.")

# --- Bot Setup ---
intents = discord.Intents.default()
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
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MAKE_WEBHOOK_URL, data=json.dumps(payload), headers=headers) as response:
                if response.status == 200:
                    await interaction.followup.send("Your query has been sent for processing.", ephemeral=True)
                else:
                    print(f"Error forwarding to Make.com. Status: {response.status}, Response: {await response.text()}")
                    await interaction.followup.send(f"An error occurred while processing your request. Status: {response.status}", ephemeral=True)
        except aiohttp.ClientError as e:
            print(f"An HTTP client error occurred: {e}")
            await interaction.followup.send("A network error occurred. Please try again later.", ephemeral=True)

@client.event
async def on_ready():
    await tree.sync(guild=GUILD_ID)
    print(f'Logged in as {client.user}')
    print('Application commands synced. Bot is ready.')

# --- Run Bot ---
client.run(BOT_TOKEN)