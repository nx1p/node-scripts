import discord
from discord.ext import commands
import sqlite3
import json
import time
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from database import create_tables

console = Console()

# Read the configuration file
with open('secrets/config.json') as f:
    config = json.load(f)
DISCORD_BOT_TOKEN = config['DISCORD_BOT_TOKEN']

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    console.print(Panel(f"[bold green]Logged in as {bot.user.name}"))
    create_tables()
    await build_database()

async def build_database():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        build_task = progress.add_task("[cyan]Building database...", total=None)
        
        for guild in bot.guilds:
            await process_guild(guild)
            progress.update(build_task, advance=1)
        
        progress.update(build_task, visible=False)
        elapsed_time = progress.tasks[0].elapsed
        console.print(Panel(f"[bold green]Database building completed in {elapsed_time:.2f} seconds."))

async def process_guild(guild):
    console.print(Panel(f"[bold blue]Processing server: {guild.name}"))
    
    # Process server
    conn = sqlite3.connect('discord_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO servers VALUES (?, ?)", (str(guild.id), guild.name))
    conn.commit()

    # Process channels
    for channel in guild.channels:
        await process_channel(channel)

    conn.close()

async def process_channel(channel):
    if isinstance(channel, discord.CategoryChannel):
        return

    try:
        console.print(f"[bold green]Processing channel: {channel.name}")
        
        conn = sqlite3.connect('discord_data.db')
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO channels VALUES (?, ?, ?, ?)",
                  (str(channel.id), channel.name, str(channel.guild.id), type(channel).__name__))
        conn.commit()
        conn.close()

        if isinstance(channel, discord.TextChannel):
            # Process messages in the text channel
            async for message in channel.history(limit=None, oldest_first=True):
                process_message(message)

        # Process active threads
        for thread in channel.threads:
            await process_thread(thread)

        # Process archived threads
        async for thread in channel.archived_threads(limit=None):
            await process_thread(thread)

    except discord.errors.Forbidden:
        console.print(f"[bold red]Skipped channel: {channel.name} (Insufficient permissions)")

async def process_thread(thread):
    console.print(f"[bold magenta]Processing thread: {thread.name}")
    
    conn = sqlite3.connect('discord_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO threads VALUES (?, ?, ?)",
              (str(thread.id), thread.name, str(thread.parent_id)))
    conn.commit()

    # Process messages in the thread
    async for message in thread.history(limit=None, oldest_first=True):
        process_message(message, is_thread_message=True)

    conn.close()

def process_message(message, is_thread_message=False):
    conn = sqlite3.connect('discord_data.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?)",
              (str(message.id), message.content, str(message.author.id),
               str(message.created_at), str(message.channel.id), is_thread_message))
    conn.commit()
    conn.close()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_thread_message = isinstance(message.channel, discord.Thread)
    process_message(message, is_thread_message)
    await bot.process_commands(message)

bot.run(DISCORD_BOT_TOKEN)
