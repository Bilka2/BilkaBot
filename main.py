import asyncio
import base64
import discord
import feedparser
import json
import sys

with open('config.json', 'r') as f:
  config = json.load(f)

sys.path.append(config['path_to_wiki_scripts'])
from analytics import main as wiki_analytics
from new_fff import main as wiki_new_fff

TOKEN = base64.b64decode(config['token']).decode('utf-8')
client = discord.Client()

with open('feeds.json', 'r') as f:
  feeds = json.load(f)

async def update_feeds():
  await client.wait_until_ready()
  while not client.is_closed:
    for name, entry in feeds.items():
      feed = feedparser.parse(entry['url'])
      if feed.entries[0].updated > entry['time_latest_entry'] and name == 'fff':
        msg = 'Ran wiki script:\n' + wiki_analytics() + '\n' + wiki_new_fff()
        channel = client.get_channel(entry['channel'])
        print(msg)
        await client.send_message(channel, msg)
        feeds[name]['time_latest_entry'] = feed.entries[0].updated
        with open('feeds.json', 'w') as f:
          json.dump(feeds, f)
    await asyncio.sleep(300)

@client.event
async def on_message(message):
  if message.author.bot:
    return
  
  if message.content.startswith('!hello'):
    msg = 'Hello {0.author.mention}'.format(message)
    await client.send_message(message.channel, msg)
  if message.content.startswith('!friday'):
    msg = wiki_analytics() + '\n' + wiki_new_fff()
    await client.send_message(message.channel, msg)

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print('------')

loop = asyncio.get_event_loop()
try:
  task = loop.create_task(update_feeds())
  loop.run_until_complete(client.start(TOKEN))
except KeyboardInterrupt:
  task.cancel()
  loop.run_until_complete(client.logout())
finally:
  loop.close()
