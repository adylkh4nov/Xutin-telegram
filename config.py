import os
from dotenv import load_dotenv

load_dotenv()

TOKEN         = os.getenv('BOT_TOKEN')
claude_token  = os.getenv('CLAUDE_TOKEN')
weather_token = os.getenv('WEATHER_TOKEN')
