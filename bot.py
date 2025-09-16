import discord
from discord.ext import commands
import os

# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.slash_command(name="predict", description="Get a football match prediction")
async def predict(ctx):
    """Slash command that returns a hard-coded match prediction"""
    prediction = "Manchester United vs Liverpool: Manchester United wins 2-1."
    await ctx.respond(prediction)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN environment variable not set")
        exit(1)
    
    bot.run(token)
