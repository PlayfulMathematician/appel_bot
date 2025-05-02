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

appel_emoji = None  # Placeholder for the :appel: emoji

@bot.event
async def on_ready():
    global appel_emoji
    appel_emoji = discord.utils.get(bot.emojis, name="appel")
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Using emoji: {appel_emoji}")

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

@bot.tree.command(name="ping", description="ping command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("PONG")

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.emoji != appel_emoji:
        return

    # Ignore reactions on the bot's own messages
    if reaction.message.author == bot.user:
        return

    users = [u async for u in reaction.users() if not u.bot]

    if len(users) == 2:
        original = reaction.message
        content = original.content if original.content else "[no text content]"

        # Forward the message content and mention the original user
        forwarded_message = f"{appel_emoji} x2\nFrom: {original.author.mention}\n{content}"

        # Check if the original message has any attachments
        if original.attachments:
            for attachment in original.attachments:
                forwarded_message += f"\n{attachment.url}"

        await original.channel.send(forwarded_message)

bot.run(TOKEN)