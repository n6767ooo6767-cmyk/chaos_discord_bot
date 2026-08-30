import os
from flask import Flask, redirect

app = Flask(__name__)

DISCORD_INSTALL_URL = os.getenv(
    "DISCORD_INSTALL_URL",
    "https://discord.com/oauth2/authorize?client_id=1543581445539495996&scope=bot%20applications.commands",
)

@app.get("/")
def home():
    return redirect(DISCORD_INSTALL_URL, code=302)

@app.get("/health")
def health():
    return {"status": "ok", "service": "chaosbot-redirect"}
