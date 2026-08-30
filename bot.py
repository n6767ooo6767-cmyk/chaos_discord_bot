import asyncio
import os
import random
import sqlite3

import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.getenv("CHAOS_DB_PATH", "chaos.db")

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


def db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                min_delay INTEGER NOT NULL DEFAULT 120,
                max_delay INTEGER NOT NULL DEFAULT 3600
            )
        """)
        connection.commit()


def get_settings(guild_id):
    with db() as connection:
        return connection.execute(
            "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
        ).fetchone()


def save_settings(guild_id, channel_id, enabled=1, min_delay=120, max_delay=3600):
    with db() as connection:
        connection.execute("""
            INSERT INTO guild_settings
                (guild_id, channel_id, enabled, min_delay, max_delay)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                enabled = excluded.enabled,
                min_delay = excluded.min_delay,
                max_delay = excluded.max_delay
        """, (guild_id, channel_id, enabled, min_delay, max_delay))
        connection.commit()


def update_enabled(guild_id, enabled):
    with db() as connection:
        connection.execute(
            "UPDATE guild_settings SET enabled = ? WHERE guild_id = ?",
            (1 if enabled else 0, guild_id),
        )
        connection.commit()


def update_delays(guild_id, minimum, maximum):
    with db() as connection:
        connection.execute(
            "UPDATE guild_settings SET min_delay = ?, max_delay = ? WHERE guild_id = ?",
            (minimum, maximum, guild_id),
        )
        connection.commit()


async def send_random_event(guild, settings):
    channel = guild.get_channel(settings["channel_id"])
    if channel is None:
        return

    roll = random.random()

    # A very rare real moderation event, guarded by Discord role hierarchy.
    if roll < 0.01:
        members = [member for member in guild.members if not member.bot]
        member = random.choice(members) if members else None
        me = guild.me

        if member and me and me.guild_permissions.kick_members:
            if member != guild.owner and member.top_role < me.top_role:
                try:
                    await member.kick(reason="ChaosBot random event")
                    await channel.send("🎲 случайное событие произошло. я ничего не объясняю.")
                    return
                except (discord.Forbidden, discord.HTTPException):
                    pass

    if roll < 0.40:
        await channel.send(random.choice(SAFE_MESSAGES))
    else:
        await channel.send(random.choice([
            "🎲 ...",
            "🤨",
            "система задумалась.",
            "ничего не произошло.",
        ]))


async def chaos_loop():
    await bot.wait_until_ready()

    while not bot.is_closed():
        configured = []
        for guild in bot.guilds:
            settings = get_settings(guild.id)
            if settings and settings["enabled"]:
                configured.append((guild, settings))

        if not configured:
            await asyncio.sleep(30)
            continue

        # One independent timer per configured guild.
        tasks = []
        for guild, settings in configured:
            delay = random.randint(settings["min_delay"], settings["max_delay"])
            tasks.append(asyncio.create_task(asyncio.sleep(delay)))

        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            index = tasks.index(task)
            guild, settings = configured[index]
            try:
                await send_random_event(guild, settings)
            except (discord.Forbidden, discord.HTTPException) as error:
                print(f"Discord error in {guild.id}: {error}")

        for task in tasks:
            if not task.done():
                task.cancel()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    if not hasattr(bot, "chaos_task") or bot.chaos_task.done():
        bot.chaos_task = asyncio.create_task(chaos_loop())


@bot.command()
@commands.has_permissions(manage_guild=True)
async def setup(ctx, channel: discord.TextChannel):
    save_settings(ctx.guild.id, channel.id)
    await ctx.send(f"🎲 канал хаоса установлен: {channel.mention}")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def chaos(ctx, action: str = "status"):
    settings = get_settings(ctx.guild.id)
    action = action.lower()

    if action == "status":
        if not settings:
            await ctx.send("❌ Сначала используй `!setup #канал`.")
            return
        state = "ON" if settings["enabled"] else "OFF"
        await ctx.send(
            f"🤖 ChaosBot: {state} | канал: <#{settings['channel_id']}> | "
            f"интервал: {settings['min_delay']}-{settings['max_delay']} сек."
        )
    elif action == "stop":
        if settings:
            update_enabled(ctx.guild.id, False)
        await ctx.send("🛑 хаос остановлен на этом сервере.")
    elif action == "start":
        if not settings:
            await ctx.send("❌ Сначала используй `!setup #канал`.")
            return
        update_enabled(ctx.guild.id, True)
        await ctx.send("🎲 хаос снова активирован на этом сервере.")
    else:
        await ctx.send("Используй `!chaos status`, `!chaos start` или `!chaos stop`.")


@bot.command()
@commands.has_permissions(manage_guild=True)
async def delay(ctx, minimum: int, maximum: int):
    settings = get_settings(ctx.guild.id)
    if not settings:
        await ctx.send("❌ Сначала используй `!setup #канал`.")
        return
    if minimum < 10 or maximum < minimum or maximum > 86400:
        await ctx.send("❌ Интервал: от 10 секунд до 24 часов.")
        return
    update_delays(ctx.guild.id, minimum, maximum)
    await ctx.send(f"⏱️ Новый интервал: {minimum}-{maximum} сек.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⛔ нужны права Manage Server.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Не хватает аргументов. Проверь команду.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Проверь аргументы команды.")
    elif not isinstance(error, commands.CommandNotFound):
        print(f"Command error: {error}")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN is not set")
    init_db()
    bot.run(TOKEN)
