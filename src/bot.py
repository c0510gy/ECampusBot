from discord.ext.commands import Bot

bot = Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} 에 로그인하였습니다!')

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

DISCORD_KEY = os.getenv("DISCORD_KEY")
bot.run(DISCORD_KEY)