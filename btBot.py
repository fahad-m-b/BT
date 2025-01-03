import discord
from discord.ext import commands
import requests
from langchain_ollama import OllamaLLM  # Llama integration

# Set up bot with `!` prefix
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True  # Enable message content for server messages
bot = commands.Bot(command_prefix="!", intents=intents)

# Llama Model setup
model = OllamaLLM(model="llama3.2:3b")

# Generate response using the Llama model
def generate_response(prompt):
    try:
        response = model.invoke({"prompt": prompt})
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

# Commands
@bot.command(name="commands")
async def commands_list(ctx):
    """Show all available commands."""
    commands_list = """
    **Available Commands**:
    - `!help`: Show this help message.
    - `!origin`: Learn about BT's origin.
    - `!manga [title]`: Search for a manga or get a random recommendation if no title is provided.
    - `!joke`: Hear a dynamic, AI-generated joke.
    - `!roulette [choices]`: Choose a random option from a list of choices (comma-separated).
    - `hey bt [message]`: Chat with BT using AI.
    """
    await ctx.send(commands_list)

@bot.command(name="origin")
async def origin(ctx):
    """Learn about BT's origin."""
    await ctx.send(
        "I am BT-7274, a Vanguard-class Titan from *Titanfall 2*. I'm back to assist and have some fun with you!"
    )

@bot.command(name="manga")
async def manga(ctx, *, title=None):
    """Search for a manga or get a random recommendation."""
    if title:
        result = search_manga(title)
        await ctx.send(result)
    else:
        result = random_manga()
        await ctx.send(result)

@bot.command(name="joke")
async def joke(ctx):
    """Generate a random joke using AI."""
    prompt = "Tell me a creative and funny joke."
    joke = generate_response(prompt)
    await ctx.send(joke)

@bot.command(name="roulette")
async def roulette(ctx, *, choices=None):
    """Choose a random option from your list."""
    if choices:
        options = choices.split(",")
        choice = random.choice(options).strip()
        await ctx.send(f"The roulette chose: {choice}!")
    else:
        await ctx.send("Please provide choices separated by commas, e.g., `!roulette soccer, chess, video games`.")

# Free-form conversation with "hey bt"
@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore messages from bots

    # Check if the message starts with "hey bt"
    if message.content.lower().startswith("hey bt"):
        query = message.content[len("hey bt"):].strip()
        response = generate_response(query)
        await message.channel.send(response)

    # Allow command processing in servers
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Bot is online and logged in as {bot.user.name}")

# Run the bot
bot.run("MTIxOTU3NjIwNjgxOTg1MjI5OA.GBNxwc.cpppEOGn-rWQEG7Hc0nylsvQ7ROlOcIs2VFbcI")