import asyncio
import base64
import datetime
import discord
import feedparser
import html
import json
import logging
import re
import requests
import sys
import time
import tomd
import traceback

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", datefmt= "%Y-%m-%d %H:%M:%S", level=logging.INFO, filename='log.log')
with open('config.json', 'r') as f:
  config = json.load(f)

sys.path.append(config['path_to_wiki_scripts'])
from analytics import main as wiki_analytics
from new_fff import main as wiki_new_fff
from new_version import main as wiki_new_version

TOKEN = base64.b64decode(config['token']).decode('utf-8')
client = discord.Client()

with open('feeds.json', 'r') as f:
  feeds = json.load(f)

async def update_feed(name, feed_data, feeds):
  await client.wait_until_ready()
  while not client.is_closed:
    try:
      await check_feed(name, feed_data, feeds)
    except:
      error_log(traceback.format_exc())
    await asyncio.sleep(feed_data['sleep_for'])

async def check_feed(name, feed_data, feeds):
  feed = feedparser.parse(feed_data['url'])
  if get_formatted_time(feed.entries[0]) > feed_data['time_latest_entry'] and name == 'fff':
    await fff_updated(name, feed_data, feed, feeds)
  elif get_formatted_time(feed.entries[0]) > feed_data['time_latest_entry'] and name == 'wiki':
    await wiki_updated(name, feed_data, feed, feeds)
  elif get_formatted_time(feed.entries[0]) > feed_data['time_latest_entry'] and name == 'forums_news':
    await forums_news_updated(name, feed_data, feed, feeds)
  else:
    info_log(f'Feed "{name}" was not updated.')

async def fff_updated(name, feed_data, feed, feeds):
  msg = 'Ran wiki script:\n' + wiki_analytics() + '\n' + wiki_new_fff()
  channel = client.get_channel(feed_data['channel'])
  info_log(msg)
  await client.send_message(channel, msg)
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)

async def wiki_updated(name, feed_data, feed, feeds):
  time_latest_entry = feed_data['time_latest_entry']
  for i, entry in enumerate(feed.entries):
    if get_formatted_time(entry) > time_latest_entry:
      info_log('Found new wiki entry made on ' + entry.updated)
      summary = ''
      if re.search('<p.*?>.*?<\/p>', entry.summary):
        summary = html.unescape(tomd.convert(re.search('<p.*?>.*?<\/p>', entry.summary).group()))
        summary = re.sub(r'\((\/\S*)\)', r'(https://wiki.factorio.com\1)', summary)
      embed = discord.Embed(title = f'{entry.author} changed {entry.title}', color = 14103594, timestamp = datetime.datetime(*entry.updated_parsed[0:6]), url = entry.link, description = summary)
      channel = client.get_channel(feed_data['channel'])
      await client.send_message(channel, embed=embed)
    else:
      break
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)

async def forums_news_updated(name, feed_data, feed, feeds):
  time_latest_entry = feed_data['time_latest_entry']
  for i, entry in enumerate(feed.entries):
    if get_formatted_time(entry) > time_latest_entry:
      is_new_version = re.search('^Version (\d\.\d+\.\d+$)', entry.title)
      if not is_new_version:
        continue
      else:
        version = is_new_version.group(1)
        reddit_url = feed_data['reddit_rss']
        reddit_entry = await get_version_entry_from_reddit(entry.title, reddit_url, 0)
        channel = client.get_channel(feed_data['channel'])
        if not reddit_entry:
          embed = discord.Embed(title = f'Version {version} is out but the reddit post could not be found.', color = 0xff0000, timestamp = datetime.datetime(*entry.updated_parsed[0:6]), url = entry.link)
          await client.send_message(channel, '<@204512563197640704>', embed=embed)
        
        webhook_url = feed_data['webhook_url']
        forum_post_number = re.search('^https:\/\/forums\.factorio\.com\/viewtopic\.php\?t=(\d+)', entry.link).group(1)
        announcement_msg = f'@here Version {version} released.\nhttps://forums.factorio.com/{forum_post_number}' + f'\n{reddit_entry.link}' if reddit_entry else ''
        info_log(announcement_msg)
        announcement = {}
        announcement['content'] = announcement_msg
        result = requests.post(webhook_url, data=json.dumps(announcement), headers={'Content-Type': 'application/json'})
        try:
          result.raise_for_status()
        except requests.exceptions.HTTPError as err:
          error_log(err)
        wiki_msg = wiki_new_version(forum_post_number, version)
        await client.send_message(channel, wiki_msg)
    else:
      break
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)

async def get_version_entry_from_reddit(entry_title, reddit_url, iteration):
  reddit_feed = feedparser.parse(reddit_url)
  for i, entry in enumerate(reddit_feed.entries):
    if entry.title == entry_title:
      return entry
    if i > 5: #limit to the 5 latests entries
      break
  #couldn't find new version on reddit
  if iteration == 8-1:
    error_log(f'Could not find reddit post for {entry_title} within 8 * 15 seconds. Aborting.')
    return False
  await asyncio.sleep(15)
  await get_version_entry_from_reddit(entry_title, reddit_url, iteration+1)

def get_formatted_time(entry):
  return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", entry.updated_parsed)

@client.event
async def on_message(message):
  if message.author.bot:
    return
  
  if message.content.startswith('!hello'):
    msg = 'Hello {0.author.mention}'.format(message)
    await client.send_message(message.channel, msg)
  if message.content.startswith('!friday') and message.author.id == '204512563197640704':
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
  tasks = []
  for name, feed_data in feeds.items():
    task = loop.create_task(update_feed(name, feed_data, feeds))
    tasks.append(task)
  loop.run_until_complete(client.start(TOKEN))
except KeyboardInterrupt:
  info_log('Received KeyboardInterrupt, logging out')
  for task in tasks:
    task.cancel()
  loop.run_until_complete(client.logout())
except:
  error_log(traceback.format_exc())
finally:
  loop.close()
