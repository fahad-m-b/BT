import discord
from discord.ext import commands
import requests
import random
import asyncio
from langchain_ollama import OllamaLLM  # Llama integration

# Set up bot with `!` prefix
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable message content for server messages
intents.members = True  # Enable member join/leave events
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Llama Model setup
model = OllamaLLM(model="llama3.2:1b", base_url="http://127.0.0.1:11434")

# Store user preferences and conversation history
user_preferences = {}
conversation_history = {}

# Generate response using the Llama model
def generate_response(prompt):
    try:
        response = model.invoke(prompt)
        return response
    except Exception as e:
        return f"Oops, something went wrong: {e}"

# MangaDex API functions
def search_manga(title):
    url = f"https://api.mangadex.org/manga?title={title}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get("data", [])
        if results:
            manga = results[0]
            manga_title = manga["attributes"]["title"]["en"]
            manga_url = f"https://mangadex.org/title/{manga['id']}"
            return f"Found: [{manga_title}]({manga_url})"
        else:
            return "No manga found with that title."
    else:
        return "Failed to contact MangaDex."

def random_manga():
    url = "https://api.mangadex.org/manga?limit=1&offset=0"
    response = requests.get(url)
    if response.status_code == 200:
        manga = response.json().get("data", [])[0]
        manga_title = manga["attributes"]["title"]["en"]
        manga_url = f"https://mangadex.org/title/{manga['id']}"
        return f"Random Manga: [{manga_title}]({manga_url})"
    else:
        return "Failed to contact MangaDex."

# Custom Help Command
@bot.command(name="help")
async def custom_help(ctx):
    """Custom help message."""
    help_message = """
    **BT Commands:**
    - `!chat [message]`: Answer questions with personality.
    - `!commands`: Show all available commands.
    - `!help`: Show this help message.
    - `!meme`: Fetch a random meme from Reddit.
    - `!origin`: Learn about BT's origin.
    - `!personality [funny/serious/neutral]`: Set the bot's personality.
    - `!poll [question] [option1, option2, ...]`: Create a poll.
    - `!remind [time] [message]`: Set a reminder.
    - `!roulette [choices]`: Choose a random option from your list.
    - `!rps [rock/paper/scissors]`: Play Rock-Paper-Scissors.
    
    Type `!command` for more information on a specific command!
    """
    await ctx.send(help_message)

@bot.command(name="commands")
async def commands_list(ctx):
    """Show all available commands."""
    commands_list = """
    **Available Commands**:
    - `!help`: Show this help message.
    - `!origin`: Learn about BT's origin.
    - `!meme`: Get a random meme.
    - `!remind [time] [message]`: Set a reminder.
    - `!rps [rock/paper/scissors]`: Play Rock-Paper-Scissors.
    - `!poll [question] [option1, option2, ...]`: Create a poll.
    - `!roulette [choices]`: Choose a random option from a list of choices.
    - `!personality [funny/serious/neutral]`: Set my personality.
    - `hey bt [message]`: Chat with BT using AI.
    """
    await ctx.send(commands_list)

@bot.command(name="origin")
async def origin(ctx):
    """Learn about BT's origin."""
    await ctx.send(
        "I am BT-7274, a Vanguard-class Titan from *Titanfall 2*. I'm back to assist and have some fun with you!"
    )

@bot.command(name="meme")
async def meme(ctx):
    """Fetch a random meme from Reddit."""
    response = requests.get("https://meme-api.herokuapp.com/gimme")
    if response.status_code == 200:
        meme = response.json()
        await ctx.send(meme["url"])
    else:
        await ctx.send("Couldn't fetch a meme right now. Try again later!")

@bot.command(name="remind")
async def remind(ctx, time: int, *, message: str):
    """Set a reminder."""
    await ctx.send(f"Okay! I'll remind you in {time} seconds.")
    await asyncio.sleep(time)
    await ctx.send(f"Reminder: {message}")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name="general")  # Replace 'general' with your welcome channel name
    if channel:
        await channel.send(f"Welcome {member.mention} to {member.guild.name}!")

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.channels, name="general")  # Replace 'general' with your goodbye channel name
    if channel:
        await channel.send(f"Goodbye {member.mention}. We'll miss you!")

@bot.command(name="rps")
async def rps(ctx, choice: str):
    """Play Rock-Paper-Scissors."""
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    if choice.lower() not in choices:
        await ctx.send("Invalid choice! Choose rock, paper, or scissors.")
        return
    if choice == bot_choice:
        result = "It's a tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "I win!"
    await ctx.send(f"I chose {bot_choice}. {result}")

@bot.command(name="poll")
async def poll(ctx, question: str, *, options: str):
    """Create a poll."""
    options = options.split(",")
    if len(options) < 2:
        await ctx.send("Please provide at least two options separated by commas.")
        return
    embed = discord.Embed(title="Poll", description=question)
    for i, option in enumerate(options, 1):
        embed.add_field(name=f"Option {i}", value=option.strip(), inline=False)
    message = await ctx.send(embed=embed)
    reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
    for i in range(len(options))
        await message.add_reaction(reactions[i])

@bot.command(name="roulette")
async def roulette(ctx, *, input: str):
    """Choose a random option from your list."""
    if "list of games" in input.lower():
        options = input.split("list of games ")[1].split(",")
    elif "character from marvel rival" in input.lower():
        options = ["Iron Man", "Spider-Man", "Hulk", "Captain Marvel", "Thanos", "Doctor Strange"]
    else:
        options = input.split(",")
    choice = random.choice(options).strip()
    await ctx.send(f"The roulette chose: {choice}!")

@bot.command(name="personality")
async def set_personality(ctx, mode: str):
    """Set the bot's personality."""
    global user_preferences
    user_preferences[ctx.author.id] = mode.lower()
    await ctx.send(f"Got it, {ctx.author.name}. I'll chat with you in {mode} mode.")

@bot.command(name="chat")
async def chat(ctx, *, question: str):
    """Answer questions with personality."""
    mode = user_preferences.get(ctx.author.id, "neutral")
    if mode == "funny":
        await ctx.send(f"Why did the chicken cross the road? To answer your question, {ctx.author.name}! 😂")
    elif mode == "serious":
        await ctx.send(f"That's a deep question, {ctx.author.name}. Let me think carefully.")
    else:
        response = generate_response(question)
        await ctx.send(response)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    # Add reactions based on message content
    if "happy" in message.content.lower():
        await message.add_reaction("😊")
    elif "sad" in message.content.lower():
        await message.add_reaction("😢")
    elif "angry" in message.content.lower():
        await message.add_reaction("😡")

    # Check if the message starts with "hey bt"
    if message.content.lower().startswith("hey bt"):
        query = message.content[len("hey bt"):].strip()
        response = generate_response(query)
        await message.channel.send(response)

    # Allow command processing in servers
    await bot.process_commands(message)

@bot.event
async def on_ready():
    status_themes = [
        discord.Game("watching over the server like Batman"),
        discord.Game("beating one of the members in chess"),
        discord.Game("thinking about memes"),
        discord.Game("running AI calculations"),
        discord.Game("watching the chaos unfold"),
    ]
    chosen_status = random.choice(status_themes)
    await bot.change_presence(activity=chosen_status)
    print(f"Bot is online and logged in as {bot.user.name}")

# Run the bot
bot.run("MTIxOTU3NjIwNjgxOTg1MjI5OA.GBNxwc.cpppEOGn-rWQEG7Hc0nylsvQ7ROlOcIs2VFbcI")
