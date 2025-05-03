import os
import requests
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# === Configuration ===
load_dotenv()
TOKEN = os.getenv("TESTING_BOT_TOKEN")
CHANNEL_ID = 1367988776781090926
CHANNEL_ID_APPELBOARD = 1368024850098294856
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

def fetch_player_pbs(player_name):
    """Fetch all personal bests for a player by username"""
    # First get the user ID from the username
    user_url = f"https://www.speedrun.com/api/v1/users?lookup={player_name}"
    try:
        user_response = session.get(user_url, timeout=5)
        user_response.raise_for_status()
        user_data = user_response.json().get("data", [])
        
        if not user_data:
            return None, f"Player '{player_name}' not found"
        
        user_id = user_data[0].get("id")
        user_name = user_data[0].get("names", {}).get("international", player_name)
        
        # Now get the PBs using the user ID with proper embedding to reduce API calls
        # Include game, category, and level data in the response using the embed parameter
        pbs_url = f"https://www.speedrun.com/api/v1/users/{user_id}/personal-bests?embed=game,category,level"
        pbs_response = session.get(pbs_url, timeout=5)
        pbs_response.raise_for_status()
        pbs_data = pbs_response.json().get("data", [])
        
        return {
            "user_name": user_name,
            "pbs": pbs_data
        }, None
    except requests.RequestException as e:
        return None, f"Error fetching data: {str(e)}"

def format_time(run_time):
    """Format the run time from Speedrun.com"""
    if not run_time:
        return "Time not available"

    # Convert PT1H23M45S format to readable format
    time_str = run_time.replace("PT", "")
    hours = 0
    minutes = 0
    seconds = 0
    milliseconds = 0
    
    # Handle hours
    if "H" in time_str:
        h_split = time_str.split("H")
        hours = int(h_split[0])
        time_str = h_split[1]
    
    # Handle minutes
    if "M" in time_str:
        m_split = time_str.split("M")
        minutes = int(m_split[0])
        time_str = m_split[1]
    
    # Handle seconds and milliseconds
    if "S" in time_str:
        s_split = time_str.split("S")[0]
        if "." in s_split:
            s_parts = s_split.split(".")
            seconds = int(s_parts[0])
            milliseconds = int(s_parts[1])
        else:
            seconds = int(s_split)
    
    # Format the time based on components
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}.{milliseconds:03d}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}.{milliseconds:03d}s"
    else:
        return f"{seconds}.{milliseconds:03d}s"

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

@bot.tree.command(name="latest_run", description="Get the latest speedrun.com run for Appel.")
async def latest_run(interaction: discord.Interaction):
    run = fetch_latest_run()
    if not run:
        await interaction.response.send_message("No runs found")
        return
    link = extract_link(run)
    await interaction.response.send_message(f"**Latest Run!**\n{link}")
    
@bot.tree.command(name="getallpbs", description="Get a player's personal best for a specific game and category")
async def get_pb(interaction: discord.Interaction, player: str, game: str, category: str = None):
    """Get a player's personal best for a specific game and category"""
    await interaction.response.defer()
    data, error = fetch_player_pbs(player)
    
    if error:
        await interaction.followup.send(f"Error: {error}")
        return
    
    user_name = data["user_name"]
    pbs = data["pbs"]  # Already contains only PBs, not obsolete runs
    
    if not pbs:
        await interaction.followup.send(f"No personal bests found for {user_name}")
        return
        
    # Filter by game name (case-insensitive partial match)
    matching_pbs = []
    for pb in pbs:
        game_data = pb.get("game", {}).get("data", {})
        game_name = game_data.get("names", {}).get("international", "Unknown Game")
        
        if game.lower() in game_name.lower():
            category_data = pb.get("category", {}).get("data", {})
            category_name = category_data.get("name", "Unknown Category")
            
            # Check if this is a level run (individual level) or a full-game run
            level_data = pb.get("level", {}).get("data", {})
            level_info = ""
            if level_data:
                level_name = level_data.get("name", "Unknown Level")
                level_info = f" {level_name}"
            
            # If category is specified, filter by it too
            if category is None or category.lower() in category_name.lower():
                matching_pbs.append({
                    "game": game_name,
                    "category": category_name,
                    "level": level_info,
                    "place": pb.get("place", 0),
                    "time": format_time(pb["run"].get("times", {}).get("primary")),
                    "date": pb["run"].get("date", "Unknown date"),
                    "link": pb["run"].get("weblink", "")
                })
    
    if not matching_pbs:
        message = f"No personal bests found for {user_name} in games matching '{game}'"
        if category:
            message += f" and category matching '{category}'"
        await interaction.followup.send(message)
        return
        
    # Sort by place (lowest number first)
    matching_pbs.sort(key=lambda x: (x["place"] if isinstance(x["place"], int) else 999))
    
    # Create embeds for results - maximum 5 messages with as many PBs as possible per message
    MAX_MESSAGES = 5
    PBs_PER_EMBED = 25  # Discord embed limit is 25 fields
    
    # Calculate how many PBs we can show with our message limit
    total_pbs_to_show = min(len(matching_pbs), MAX_MESSAGES * PBs_PER_EMBED)
    
    # Create list to hold our embeds
    embeds = []
    
    # Create embeds, each with up to PBs_PER_EMBED fields
    for i in range(0, total_pbs_to_show, PBs_PER_EMBED):
        # Get the chunk of PBs for this embed
        embed_pbs = matching_pbs[i:min(i+PBs_PER_EMBED, total_pbs_to_show)]
        
        # Create the embed
        embed = discord.Embed(
            title=f"Personal Bests for {user_name}" + (f" (Page {i//PBs_PER_EMBED + 1})" if i > 0 else ""),
            color=discord.Color.gold()
        )
        
        # Add fields for each PB
        for pb in embed_pbs:
            emoji = "🥇" if pb["place"] == 1 else "🥈" if pb["place"] == 2 else "🥉" if pb["place"] == 3 else f"#{pb['place']}"
            value = f"[{emoji} **Time:** {pb['time']}\n]({pb['link']})"
            embed.add_field(name=f"{pb['game']} - {pb['category']}{pb['level']}", value=value, inline=False)
        
        embeds.append(embed)
    
    # Add footer to the last embed if we didn't show all PBs
    if len(matching_pbs) > total_pbs_to_show:
        embeds[-1].set_footer(text=f"Showing {total_pbs_to_show} of {len(matching_pbs)} matching results")
    
    # Send the embeds
    for embed in embeds:
        await interaction.followup.send(embed=embed)

@bot.tree.command(name="pbs", description="Get a player's personal bests from speedrun.com")
async def get_pbs(interaction: discord.Interaction, player: str, game: str = None, showall: bool = False):
    """Get all personal bests for a player, optionally filtered by game name"""
    await interaction.response.defer()
    data, error = fetch_player_pbs(player)
    
    if error:
        await interaction.followup.send(f"Error: {error}")
        return
    
    user_name = data["user_name"]
    pbs = data["pbs"]
    
    if not pbs:
        await interaction.followup.send(f"No personal bests found for {user_name}")
        return
    
    # Group PBs by game
    games = {}
    for pb in pbs:
        # Get game info from embedded data
        game_data = pb.get("game", {}).get("data", {})
        game_id = game_data.get("id", "unknown")
        game_name = game_data.get("names", {}).get("international", "Unknown Game")
        
        # Filter by game name if specified
        if game and game.lower() not in game_name.lower():
            continue
            
        if game_id not in games:
            games[game_id] = {
                "name": game_name,
                "runs": []
            }
        
        # Get category name from embedded data
        category_data = pb.get("category", {}).get("data", {})
        category_name = category_data.get("name", "Unknown Category")
        
        # Check if this is a level run (individual level) or a full-game run
        level_data = pb.get("level", {}).get("data", {})
        level_info = ""
        if level_data:
            level_name = level_data.get("name", "Unknown Level")
            level_info = f" (Level: {level_name})"
        
        # Format the run information
        place = pb.get("place", 0)
        time = format_time(pb["run"].get("times", {}).get("primary"))
        date = pb["run"].get("date", "Unknown date")
        run_link = pb["run"].get("weblink", "")
        
        games[game_id]["runs"].append({
            "category": category_name,
            "level": level_info,
            "place": place,
            "time": time,
            "date": date,
            "link": run_link
        })
    
    # Check if any runs match the filter
    if game and not games:
        await interaction.followup.send(f"No personal bests found for {user_name} in games matching '{game}'")
        return
    
    # Sort games by name
    sorted_games = dict(sorted(games.items(), key=lambda x: x[1]["name"]))
    
    # Maximum number of messages to send
    MAX_MESSAGES = 5
    
    # Maximum runs to show per game if not showing all
    DEFAULT_RUNS_PER_GAME = 5
    
    # Maximum fields per embed
    MAX_FIELDS_PER_EMBED = 25
    
    # Track how many messages we've sent
    message_count = 0
    
    # Prepare a list to hold content for each message
    embeds_to_send = []
    
    # Create the main overview embed
    overview_embed = discord.Embed(
        title=f"Personal Bests for {user_name}",
        color=discord.Color.gold(),
        url=f"https://www.speedrun.com/users/{user_name}",
        description=f"Found PBs in {len(sorted_games)} games." + 
                    (f" Filtered by game: '{game}'" if game else "")
    )
    embeds_to_send.append(overview_embed)
    
    # Process each game
    field_count = 0
    for game_id, game_data in sorted_games.items():
        game_name = game_data["name"]
        
        # Sort runs by place
        sorted_runs = sorted(game_data["runs"], key=lambda x: (x["place"] if isinstance(x["place"], int) else 999))
        
        runs_text = ""
        # Determine how many runs to show
        display_count = len(sorted_runs) if showall else min(DEFAULT_RUNS_PER_GAME, len(sorted_runs))
        
        for run in sorted_runs[:display_count]:
            emoji = "🥇" if run["place"] == 1 else "🥈" if run["place"] == 2 else "🥉" if run["place"] == 3 else f"#{run['place']}"
            run_line = f"**{run['category']}{run['level']}**: {emoji} {run['time']} ([Link]({run['link']}))\n"
            
            # Check if adding this line would exceed Discord's field value limit
            if len(runs_text) + len(run_line) > 1000:
                runs_text += f"*...and more categories*\n"
                break
                
            runs_text += run_line
        
        if not showall and len(sorted_runs) > DEFAULT_RUNS_PER_GAME:
            runs_text += f"*...and {len(sorted_runs) - DEFAULT_RUNS_PER_GAME} more categories*\n"
        
        # If this field would put us over the limit, create a new embed
        if field_count >= MAX_FIELDS_PER_EMBED:
            # Check if we've hit our message limit
            if len(embeds_to_send) >= MAX_MESSAGES:
                # We can't add any more embeds, so add a note to the last embed
                embeds_to_send[-1].add_field(
                    name="Message Limit Reached",
                    value=f"There are more games not shown due to the message limit. Try filtering by game name.",
                    inline=False
                )
                break
                
            # Create a new embed for overflow
            new_overview = discord.Embed(
                title=f"Personal Bests for {user_name} (continued)",
                color=discord.Color.gold(),
                url=f"https://www.speedrun.com/users/{user_name}"
            )
            embeds_to_send.append(new_overview)
            field_count = 0
            overview_embed = new_overview
        
        # Add the field to the current embed
        overview_embed.add_field(name=f"{game_name} ({len(sorted_runs)} categories)", value=runs_text, inline=False)
        field_count += 1
    
    # Send the embeds (up to MAX_MESSAGES)
    for embed in embeds_to_send[:MAX_MESSAGES]:
        if message_count < MAX_MESSAGES:
            await interaction.followup.send(embed=embed)
            message_count += 1
    
    # If there would have been more messages but we hit the limit, add a note
    if len(embeds_to_send) > MAX_MESSAGES:
        await interaction.followup.send(f"Note: Some results were omitted due to message limits. Try filtering by game name.")
        message_count += 1

@bot.tree.command(name="pbsummary", description="Get a summary of a player's personal bests")
async def get_pbs_summary(interaction: discord.Interaction, player: str):
    """Gets a summary of how many games and categories a player has PBs in"""
    await interaction.response.defer()
    data, error = fetch_player_pbs(player)
    
    if error:
        await interaction.followup.send(f"Error: {error}")
        return
    
    user_name = data["user_name"]
    pbs = data["pbs"]
    
    if not pbs:
        await interaction.followup.send(f"No personal bests found for {user_name}")
        return
        
    # Count games and categories
    games = {}
    total_first_places = 0
    total_top_3 = 0
    
    for pb in pbs:
        game_data = pb.get("game", {}).get("data", {})
        game_id = game_data.get("id", "unknown")
        game_name = game_data.get("names", {}).get("international", "Unknown Game")
        
        if game_id not in games:
            games[game_id] = {
                "name": game_name,
                "categories": 0,
                "first_places": 0,
                "top_3": 0
            }
        
        games[game_id]["categories"] += 1
        
        place = pb.get("place", 0)
        if place == 1:
            games[game_id]["first_places"] += 1
            games[game_id]["top_3"] += 1
            total_first_places += 1
            total_top_3 += 1
        elif place in [2, 3]:
            games[game_id]["top_3"] += 1
            total_top_3 += 1
    
    # Create an embed for the summary
    embed = discord.Embed(
        title=f"Speedrun Summary for {user_name}",
        color=discord.Color.gold(),
        url=f"https://www.speedrun.com/users/{user_name}"
    )
    
    # Add overall stats
    embed.add_field(
        name="Overall Stats", 
        value=f"**Total Games:** {len(games)}\n"
              f"**Total Categories:** {len(pbs)}\n"
              f"**Total World Records:** {total_first_places}\n"
              f"**Total Podium Placements:** {total_top_3}",
        inline=False
    )
    
    # Find top games by category count
    top_games = sorted(games.values(), key=lambda x: x["categories"], reverse=True)[:5]
    
    # Add top games field
    top_games_text = ""
    for game in top_games:
        top_games_text += f"**{game['name']}**: {game['categories']} categories, {game['first_places']} WRs\n"
    
    embed.add_field(name="Most Active Games", value=top_games_text, inline=False)
    
    # Find games with most world records
    wr_games = sorted(games.values(), key=lambda x: x["first_places"], reverse=True)[:5]
    wr_games = [g for g in wr_games if g["first_places"] > 0]
    
    if wr_games:
        wr_text = ""
        for game in wr_games:
            wr_text += f"**{game['name']}**: {game['first_places']} WRs\n"
        
        embed.add_field(name="Most World Records", value=wr_text, inline=False)
    
    await interaction.followup.send(embed=embed)

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
        if message.author.id in [1246624937066758167, 997270873847382126]:
            for emoji in ["⬆️", "😎"]:
                await message.add_reaction(emoji)
        else:
            for emoji in ["🇸", "🇭", "🇺", "🇹"]:
                await message.add_reaction(emoji)
    await bot.process_commands(message)

forwarded_messages = set()

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot or reaction.emoji != appel_emoji:
        return
    message = reaction.message

    if message.id in forwarded_messages:
        return
    if message.author == bot.user:
        return
    channel = reaction.message.channel
    guild = channel.guild

    starboard_channel = discord.utils.get(guild.text_channels, name="appelboard")
    
    if True or len(users) >= amount:
        embed = discord.Embed(
            description=reaction.message.content,
            color=discord.Color.gold()
        )

        embed.set_author(name=str(reaction.message.author), icon_url=reaction.message.author.display_avatar.url)
        embed.add_field(name="", value=f"[Jump to message]({reaction.message.jump_url})")
        if reaction.message.attachments:
            embed.set_image(url=reaction.message.attachments[0].url)

        await starboard_channel.send(embed=embed)
        forwarded_messages.add(message.id)


# === Run Bot ===
bot.run(TOKEN)