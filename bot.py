import os
import random
import asyncio
from datetime import timedelta

import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHAOS_CHANNEL_ID", "0"))
MIN_DELAY = int(os.getenv("MIN_DELAY", "120"))
MAX_DELAY = int(os.getenv("MAX_DELAY", "3600"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

SAFE_MESSAGES = [
    "кто-нибудь видел мой тапок 💀",
    "я провёл анализ сервера. результаты засекречены.",
    "всё нормально. наверное.",
    "кто поставил этот сервер на паузу",
    "система работает штатно. это подозрительно.",
]

async def get_channel():
    if not CHANNEL_ID:
        return None
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        try:
            channel = await bot.fetch_channel(CHANNEL_ID)
        except discord.HTTPException:
            return None
    return channel

async def choose_member(guild):
    members = [m for m in guild.members if not m.bot]
    return random.choice(members) if members else None

async def try_real_action(guild):
    member = await choose_member(guild)
    if member is None:
        return False

    me = guild.me
    if me is None or not me.guild_permissions.kick_members:
        return False
    if member == guild.owner or member.top_role >= me.top_role:
        return False

    action = random.choice(["kick", "timeout"])
    try:
        if action == "kick":
            await member.kick(reason="ChaosBot random event")
        else:
            await member.timeout(timedelta(minutes=1), reason="ChaosBot random event")
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False

async def chaos_loop():
    await bot.wait_until_ready()
    while not bot.is_closed():
        delay = random.randint(max(1, MIN_DELAY), max(MIN_DELAY, MAX_DELAY))
        await asyncio.sleep(delay)

        channel = await get_channel()
        if channel is None:
            continue

        roll = random.random()
        if roll < 0.01:
            acted = await try_real_action(channel.guild)
            if acted:
                await channel.send("🎲 случайное событие завершено. я ничего не объясняю.")
        elif roll < 0.35:
            await channel.send(random.choice(SAFE_MESSAGES))
        else:
            await channel.send(random.choice([
                "🎲 *рандомное событие прошло мимо...*",
                "...",
                "🤨",
                "система задумалась.",
            ]))

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    if not any(t.get_name() == "chaos-loop" for t in asyncio.all_tasks()):
        asyncio.create_task(chaos_loop(), name="chaos-loop")

@bot.command()
@commands.has_permissions(manage_guild=True)
async def chaos(ctx, action: str = "status"):
    action = action.lower()
    if action == "status":
        await ctx.send(f"🤖 ChaosBot online. Интервал: {MIN_DELAY}-{MAX_DELAY} сек.")
    elif action == "stop":
        for task in asyncio.all_tasks():
            if task.get_name() == "chaos-loop":
                task.cancel()
        await ctx.send("🛑 хаос остановлен.")
    elif action == "start":
        if not any(t.get_name() == "chaos-loop" for t in asyncio.all_tasks()):
            asyncio.create_task(chaos_loop(), name="chaos-loop")
        await ctx.send("🎲 хаос снова активирован.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ нужны права Manage Server.")
    elif isinstance(error, commands.CommandNotFound):
        return
    else:
        print(f"Command error: {error}")

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set")
    bot.run(TOKEN)
