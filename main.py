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
@bot.command(name="sync")
async def sync(ctx):
    if ctx.author.id == 1246624937066758167:
        await ctx.send("Syncing...")
        await bot.tree.sync()
        await ctx.send("Synced!")
@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and message.author != bot.user:
        
        await message.add_reaction("🇸")
        await message.add_reaction("🇭")
        await message.add_reaction("🇺")
        await message.add_reaction("🇹")
    await bot.process_commands(message)
@bot.tree.command(name="test", description="this is a test slash command.")
async def test(interaction: discord.Interaction, input: int): # input which requires you give an integer
    await interaction.response.send_message(f"You input {input}.")


    
    
bot.run(TOKEN)