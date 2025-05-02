import os
import requests
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# === Configuration ===
load_dotenv()
TOKEN = os.getenv("TESTING_BOT_TOKEN")
CHANNEL_ID = 1367988776781090926
GAME_ID = "v1pxo8m6"
amount = 2

# === Intents ===
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# === Global Variables ===
session = requests.Session()
last_run_id = None
appel_emoji = None
forwarded_messages = set()

# === Speedrun.com Feature ===
def fetch_latest_run():
    url = f"https://www.speedrun.com/api/v1/runs?game={GAME_ID}&orderby=submitted&direction=desc&max=1"
    response = session.get(url, timeout=5)
    response.raise_for_status()
    return response.json().get("data", [None])[0]

def extract_link(run):
    return run.get("weblink", "No link available") if run else None

@tasks.loop(seconds=5)
async def check_new_run():
    global last_run_id
    run = fetch_latest_run()
    if not run:
        print("No run found.")
        return

    current_run_id = run.get("id")
    if current_run_id == last_run_id:
        return

    last_run_id = current_run_id
    link = extract_link(run)

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(f"🎉 **New Run!**\n{link}")
    else:
        print("Channel not found.")

# === Events and Commands ===
@bot.event
async def on_ready():
    global appel_emoji
    appel_emoji = discord.utils.get(bot.emojis, name="appel")
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Using emoji: {appel_emoji}")
    check_new_run.start()

@bot.command(name="latest_run")
async def latest_run(ctx):
    run = fetch_latest_run()
    if not run:
        await ctx.send("No runs found for the specified game.")
        return
    link = extract_link(run)
    await ctx.send(f"**Latest Run!**\n{link}")

@bot.command(name="sync")
async def sync(ctx):
    if ctx.author.id in [1246624937066758167, 997270873847382126]:
        await ctx.send("Syncing...")
        await bot.tree.sync()
        await ctx.send("Synced!")

@bot.tree.command(name="ping", description="ping command")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("PONG")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message) and message.author != bot.user:
        for emoji in ["🇸", "🇭", "🇺", "🇹"]:
            await message.add_reaction(emoji)
    await bot.process_commands(message)

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.emoji != appel_emoji:
        return

    message = reaction.message

    if message.id in forwarded_messages:
        return

    if message.author == bot.user:
        return

    users = [u async for u in reaction.users() if not u.bot]

    if len(users) >= amount:
        forwarded_messages.add(message.id)
        content = message.content or "[no text content]"
        forwarded_message = f"{appel_emoji} x{amount}\nFrom: {message.author.mention}\n{content}"

        if message.attachments:
            for attachment in message.attachments:
                forwarded_message += f"\n{attachment.url}"

        await message.channel.send(forwarded_message)

# === Run Bot ===
bot.run(TOKEN)