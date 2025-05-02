import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TESTING_BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send("Pong!")
@bot.command(name="ddededodediamante")
async def ddededodediamante(ctx):
    await ctx.message.reply("ddededodediamante")
@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and message.author != bot.user:
        
        await message.add_reaction("🇸")
        await message.add_reaction("🇭")
        await message.add_reaction("🇺")
        await message.add_reaction("🇹")



    
    await bot.process_commands(message)
bot.run(TOKEN)