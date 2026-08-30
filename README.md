# Chaos Discord Bot 🤖🎲

A Discord bot that waits for random amounts of time and performs random events independently on every configured server.

## Environment variables

Only the bot token is required:

- `DISCORD_TOKEN` — Discord bot token.
- `CHAOS_DB_PATH` — optional SQLite database path (default: `chaos.db`).

There is **no global `CHAOS_CHANNEL_ID`**. Each Discord server stores its own channel and settings in SQLite.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set `DISCORD_TOKEN` in your environment.
3. Start the bot:

```bash
python bot.py
```

4. On each server, a manager runs:

```text
!setup #chaos
```

The bot saves that server's channel in the database. You do not need one environment variable per server.

## Commands

Managers with **Manage Server** can use:

- `!setup #channel` — configure the random-event channel for this server.
- `!chaos status` — show this server's configuration.
- `!chaos start` — enable chaos on this server.
- `!chaos stop` — disable chaos on this server.
- `!delay 120 3600` — configure the random interval in seconds.

## Scaling model

Configuration is keyed by Discord `guild_id`:

```text
Discord server A -> channel A -> settings A
Discord server B -> channel B -> settings B
Discord server C -> channel C -> settings C
```

The bot uses one shared database instead of environment variables for individual servers.

## Permissions and safety

The bot only performs moderation actions when Discord permissions and role hierarchy allow them. It never targets bots or the server owner, and it cannot act on a member whose highest role is equal to or above the bot's highest role.

Enable only the Discord permissions you are comfortable giving the bot.
