import os
import sys

from dotenv import load_dotenv
import discord
from discord.ext import commands


def main() -> None:
    # Load environment variables from a local .env file if present
    load_dotenv()

    token = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
    if not token:
        print("[ERROR] Bot token not found. Set DISCORD_BOT_TOKEN or DISCORD_TOKEN in your environment or .env file.")
        print("        .env example: DISCORD_BOT_TOKEN=your-bot-token")
        sys.exit(1)

    # Discord Intents: message_content must be enabled in the Developer Portal for your bot
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        guilds = ", ".join(g.name for g in bot.guilds) or "No guilds"
        print(f"[READY] Logged in as {bot.user} (ID: {bot.user.id}) | Guilds: {guilds}")

    @bot.command(name="ping", help="Simple health check")
    async def ping(ctx: commands.Context):
        await ctx.reply("Pong! 🏓")

    bot.run(token)


if __name__ == "__main__":
    main()
