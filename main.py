import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
TOKEN = os.getenv("TESTING_BOT_TOKEN")

if not TOKEN:
    raise ValueError("No token provided. Set the DISCORD_BOT_TOKEN in your .env file.")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
