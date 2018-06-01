import asyncio
import base64
import discord
import feedparser
import json
import logging
import sys
import time
import traceback

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", datefmt= "%Y-%m-%d %H:%M:%S", level=logging.INFO, filename='log.log')
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
    try:
      await check_feeds()
    except:
      error_log(traceback.format_exc())
    await asyncio.sleep(60)

async def check_feeds():
  debug_print('Checking feeds')
  for name, entry in feeds.items():
    feed = feedparser.parse(entry['url'])
    if feed.entries[0].updated > entry['time_latest_entry'] and name == 'fff':
      msg = 'Ran wiki script:\n' + wiki_analytics() + '\n' + wiki_new_fff()
      channel = client.get_channel(entry['channel'])
      info_log(msg)
      await client.send_message(channel, msg)
      feeds[name]['time_latest_entry'] = feed.entries[0].updated
      with open('feeds.json', 'w') as f:
        json.dump(feeds, f)
    else:
      info_log(f'Feed "{name}" was not updated.')

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
  info_log('Logged in as')
  info_log(client.user.name)
  info_log('------')

def error_log(msg):
  print(time.asctime() + ' ' + msg)
  logging.error(msg)

def info_log(msg):
  print(time.asctime() + ' ' + msg)
  logging.info(msg)
  
def debug_print(msg):
  print(time.asctime() + ' ' + msg)

loop = asyncio.get_event_loop()
try:
  task = loop.create_task(update_feeds())
  loop.run_until_complete(client.start(TOKEN))
except KeyboardInterrupt:
  info_log('Received KeyboardInterrupt, logging out')
  task.cancel()
  loop.run_until_complete(client.logout())
except:
  error_log(traceback.format_exc())
finally:
  loop.close()
