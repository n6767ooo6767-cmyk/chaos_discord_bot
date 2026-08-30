# Chaos Discord Bot 🤖🎲

A Discord bot that waits for a random amount of time and then performs a random event.

## Environment variables

- `DISCORD_TOKEN` — Discord bot token.
- `CHAOS_CHANNEL_ID` — channel where random events happen.
- `MIN_DELAY` — minimum wait in seconds (default `120`).
- `MAX_DELAY` — maximum wait in seconds (default `3600`).

## Run locally

```bash
pip install -r requirements.txt
python bot.py
```

The bot needs the Discord intents required by the features you enable in the Discord Developer Portal.

## Controls

Server managers can use:

- `!chaos status`
- `!chaos stop`
- `!chaos start`

The bot will never target the server owner and will not act on members whose highest role is equal to or higher than the bot's role.
