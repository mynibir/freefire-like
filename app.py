import os
import logging
from threading import Thread
from datetime import datetime

from dotenv import load_dotenv
import discord
from discord.ext import commands, tasks
import aiohttp
from flask import Flask

load_dotenv()

app = Flask("")

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)

class Seemu(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents)
        self.session = None  # aiohttp session shared for cogs

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension("cogs.likeCommands")
        self.update_activity.start()

    @tasks.loop(minutes=5)
    async def update_activity(self):
        await self.wait_until_ready()
        await self.change_presence(activity=discord.Game(name="Quantum Corporation"))

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} at {datetime.now()}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"Please wait {error.retry_after:.1f} seconds before reusing this command.", mention_author=False)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply("You don't have permission to do that.", mention_author=False)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.reply(f"Missing argument: {error.param}", mention_author=False)
        elif isinstance(error, commands.CommandNotFound):
            # ignore unknown commands
            pass
        else:
            logging.error(f"Unhandled error: {error}", exc_info=True)
            await ctx.reply("An unexpected error occurred.", mention_author=False)

    async def close(self):
        if self.session:
            await self.session.close()
        await super().close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    bot = Seemu()

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise Exception("Missing DISCORD_BOT_TOKEN in environment variables.")

    try:
        bot.run(token)
    except Exception as e:
        logging.error(f"Bot crashed: {e}", exc_info=True)
