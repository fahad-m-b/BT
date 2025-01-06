import discord
from discord.ext import commands, tasks
import asyncio
import random
import sqlite3
import json
from datetime import datetime, timedelta
from langchain_ollama import OllamaLLM  # Llama integration
import os

# Bot setup
BOT_TOKEN = os.getenv("MTIxOTU3NjIwNjgxOTg1MjI5OA.GBNxwc.cpppEOGn-rWQEG7Hc0nylsvQ7ROlOcIs2VFbcI")
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Llama Model setup
model = OllamaLLM(model="llama3.2:1b", base_url="http://127.0.0.1:11434")

# SQLite database setup
conn = sqlite3.connect("bt_memory.db")
cursor = conn.cursor()

# Create tables for persistent session data
cursor.execute("""
CREATE TABLE IF NOT EXISTS user_memory (
    user_id TEXT PRIMARY KEY,
    chat_history TEXT
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS session_preferences (
    user_id TEXT PRIMARY KEY,
    timeout INTEGER DEFAULT 5
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS group_sessions (
    channel_id INTEGER PRIMARY KEY,
    active BOOLEAN DEFAULT 1
)
""")
conn.commit()

# Active chat sessions
active_sessions = {}  # {channel_id: {"users": [user_id, ...], "last_active": timestamp, "timeout": minutes}}

# Default session timeout in minutes
DEFAULT_TIMEOUT = 5

# =======================
# Helper Functions
# =======================

def get_user_timeout(user_id):
    """Retrieve a user's custom timeout from the database."""
    cursor.execute("SELECT timeout FROM session_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else DEFAULT_TIMEOUT

def set_user_timeout(user_id, timeout):
    """Save a user's custom timeout to the database."""
    cursor.execute("""
    INSERT OR REPLACE INTO session_preferences (user_id, timeout)
    VALUES (?, ?)
    """, (user_id, timeout))
    conn.commit()

def generate_response_with_memory(user_id, prompt):
    """Generate a response using user-specific chat history."""
    cursor.execute("SELECT chat_history FROM user_memory WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    history = json.loads(row[0]) if row else []

    context = "\n".join([f"User: {h['message']}\nBT: {h['response']}" for h in history[-5:]])
    full_prompt = (
        "You are BT, a fun and interactive chatbot. You know that the user and their friends love video games, anime, "
        "and memes. You enjoy teasing them playfully while staying friendly and approachable.\n\n"
        f"Prior context:\n{context}\nUser: {prompt}\nBT:"
    )

    try:
        response = model.invoke(full_prompt).strip()
        history.append({"message": prompt, "response": response})
        cursor.execute("""
        INSERT OR REPLACE INTO user_memory (user_id, chat_history)
        VALUES (?, ?)
        """, (user_id, json.dumps(history)))
        conn.commit()
        return response
    except Exception as e:
        return f"Oops, something went wrong: {e}"

# =======================
# Commands
# =======================

@bot.command(name="remind")
async def remind(ctx, time: int, *, message: str):
    """Set a reminder."""
    await ctx.send(f"Okay! I'll remind you in {time} seconds, {ctx.author.mention}.")
    await asyncio.sleep(time)
    await ctx.send(f"Reminder for {ctx.author.mention}: {message}")

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
    for i in range(len(options)):
        await message.add_reaction(reactions[i])

@bot.command(name="roulette")
async def roulette(ctx, *, input: str):
    """Choose a random option from your list."""
    options = input.split(",")
    choice = random.choice(options).strip()
    await ctx.send(f"The roulette chose: {choice}!")

@bot.command(name="meme")
async def meme(ctx):
    """Generate a meme caption and fetch a random meme image."""
    prompt = "You are a witty bot. Generate a funny and creative meme caption about gaming, anime, or memes."
    try:
        caption = model.invoke(prompt).strip()
        response = requests.get("https://meme-api.herokuapp.com/gimme")
        if response.status_code == 200:
            meme = response.json()
            await ctx.send(f"{caption}\n{meme['url']}")
        else:
            await ctx.send(f"{caption}\n(Sorry, no meme available at the moment.)")
    except Exception as e:
        await ctx.send(f"Oops, something went wrong: {e}")

@bot.command(name="joke")
async def joke(ctx):
    """Generate a funny joke."""
    prompt = "You are a humorous bot. Generate a funny joke about gaming, anime, or memes."
    try:
        joke = model.invoke(prompt).strip()
        await ctx.send(joke)
    except Exception as e:
        await ctx.send(f"Oops, something went wrong: {e}")

@bot.command(name="help")
async def custom_help(ctx):
    """Display the bot's help message with detailed descriptions of each command."""
    help_message = """
    **BT Commands:**
    - **Chat Commands**:
      - `hey bt`: Start a personal chat session with BT.
      - `bye bt`: End your chat session with BT.
    - **Group Chat Commands**:
      - `!start_chat`: Start a group chat in the current channel.
      - `!end_chat`: End the group chat in the current channel.
    - **Games and Fun**:
      - `!rps [rock/paper/scissors]`: Play Rock-Paper-Scissors.
      - `!poll [question] [option1, option2, ...]`: Create a poll.
      - `!roulette [options]`: Choose a random option.
      - `!meme`: Generate a funny meme caption and fetch a random meme.
      - `!joke`: Hear a funny AI-generated joke.
    - **Utilities**:
      - `!remind [time in seconds] [message]`: Set a reminder.
      - `!set_timeout [minutes]`: Customize your chat session timeout.
    - **Help**:
      - `!help`: Display this help message.
    """
    await ctx.send(help_message)

# =======================
# Chat Logic and Event Handlers
# =======================

@bot.event
async def on_message(message):
    """Handle user messages."""
    if message.author.bot:
        return  # Ignore messages from bots

    user_id = message.author.id
    channel_id = message.channel.id
    content = message.content.lower()

    # If "hey bt" is mentioned, add user to group session
    if content.startswith("hey bt"):
        if channel_id in active_sessions:
            if user_id not in active_sessions[channel_id]["users"]:
                active_sessions[channel_id]["users"].append(user_id)
                await message.channel.send(f"{message.author.name} has joined the group chat!")
        else:
            await message.channel.send("No active group chat session. Say `!start_chat` to begin one.")
        return

    # If user says "bye bt", remove them from the session
    if content == "bye bt":
        if channel_id in active_sessions and user_id in active_sessions[channel_id]["users"]:
            active_sessions[channel_id]["users"].remove(user_id)
            await message.channel.send(f"{message.author.name} has left the group chat!")
            if not active_sessions[channel_id]["users"]:
                del active_sessions[channel_id]
                cursor.execute("DELETE FROM group_sessions WHERE channel_id = ?", (channel_id,))
                conn.commit()
        else:
            await message.channel.send("You're not part of any active chat session.")
        return

    # Process messages for active group chat users
    if channel_id in active_sessions and user_id in active_sessions[channel_id]["users"]:
        active_sessions[channel_id]["last_active"] = datetime.now()
        response = generate_response_with_memory(user_id, message.content)
        await message.channel.send(response)
        return

    # Process commands normally
    await bot.process_commands(message)

@tasks.loop(seconds=60)
async def check_inactive_sessions():
    """Automatically end group chat sessions after inactivity."""
    now = datetime.now()
    for channel_id, session in list(active_sessions.items()):
        timeout = session["timeout"]
        last_active = session["last_active"]

        if now - last_active > timedelta(minutes=timeout):
            # End the session
            del active_sessions[channel_id]
            cursor.execute("DELETE FROM group_sessions WHERE channel_id = ?", (channel_id,))
            conn.commit()

            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send("Group chat session ended due to inactivity. Say `!start_chat` to start a new session.")

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user.name}")
    check_inactive_sessions.start()

# =======================
# Run the Bot
# =======================

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("Error: Bot token is missing. Set it as an environment variable.")
