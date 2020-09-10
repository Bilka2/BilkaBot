import asyncio
import base64
from bs4 import BeautifulSoup
import datetime
import discord
import feedparser
import html
import json
import logging
import re
import requests
import sys
import textwrap
import time
import tomd
import traceback

with open('config.json', 'r') as f:
  config = json.load(f)
sys.path.append(config['path_to_wiki_scripts'])

from analytics import main as wiki_analytics
from new_fff import main as wiki_new_fff
from new_version import main as wiki_new_version
from redirects import main as wiki_redirects
from wanted_pages import main as wiki_wanted_pages

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", datefmt= "%Y-%m-%d %H:%M:%S", level=logging.WARNING, filename='log.log')
TOKEN = base64.b64decode(config['token']).decode('utf-8')
WIKI_EDITOR_ROLE_ID = 467029685914828829
client = discord.Client()
with open('feeds.json', 'r') as f:
  feeds = json.load(f)


async def update_feed(name, feed_data, feeds):
  await client.wait_until_ready()
  while not client.is_closed():
    try:
      await check_feed(name, feed_data, feeds)
    except:
      error_log(traceback.format_exc())
    await asyncio.sleep(feed_data['sleep_for'])


async def check_feed(name, feed_data, feeds):
  feed = await loop.run_in_executor(None, feedparser.parse, feed_data['url'])
  if len(feed.entries) == 0:
    error_log(f'Feed "{name}" returned empty list of feed entries.')
    return
  if get_formatted_time(feed.entries[0]) > feed_data['time_latest_entry']:
    if name == 'fff':
      await fff_updated(name, feed_data, feed, feeds)
    elif name == 'alt-f4':
      await community_fff_updated(name, feed_data, feed, feeds)
    elif name == 'wiki':
      await wiki_updated(name, feed_data, feed, feeds)
    elif name == 'forums_news':
      await forums_news_updated(name, feed_data, feed, feeds)
    elif name == 'subreddit':
      await subreddit_updated(name, feed_data, feed, feeds)
  else:
    info_log(f'Feed "{name}" was not updated.')


async def subreddit_updated(name, feed_data, feed, feeds):
  time_latest_entry = feed_data['time_latest_entry']
  for i, entry in enumerate(feed.entries):
    if get_formatted_time(entry) > time_latest_entry:
      summary = ''
      if re.search('<p.*?>.*?<\/p>', entry.content[0].value):
        summary = html.unescape(tomd.convert(re.search('<p.*?>.*?<\/p>', entry.summary).group()))
        if entry.content[0].value.count('</p>') > 1:
          summary += '\n[...]'
      elif '<!-- SC_OFF -->' in entry.content[0].value:
        summary = html.unescape(tomd.convert(re.search('<!-- SC_OFF -->(.+)<!-- SC_ON -->', entry.content[0].value).group(1)))
        
      title = entry.title
      if len(entry.title) >= 250:
        title = textwrap.wrap(entry.title, 250)[0] + ' ...'
      
      embed = discord.Embed(title = title, color = 14103594, timestamp = datetime.datetime(*entry.updated_parsed[0:6]), url = entry.link, description = summary)
      
      link_after_user = re.search('/u/\S+ </a> <br/> <span><a href="(\S+)"', entry.content[0].value)

      if link_after_user and link_after_user.group(1) != entry.link and re.search('\.(jpg|png)$', link_after_user.group(1)):
        embed.set_image(url=link_after_user.group(1))
      elif 'img src="' in entry.content[0].value and re.search('img src="(\S+)"', entry.content[0].value):
        embed.set_thumbnail(url=(re.search('img src="(\S+)"', entry.content[0].value).group(1)))
      
      embed.set_author(name=entry.author, url=entry.author_detail.href)
      channel = client.get_channel(feed_data['channel'])
      await channel.send(embed=embed)
    else:
      break
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)
  

async def fff_updated(name, feed_data, feed, feeds):
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)
  
  entry = feed.entries[0]
  
  channel = client.get_channel(feed_data['channel'])
  await channel.send(entry.title)
  
  announcement = {}
  announcement['content'] = f'@here {entry.title}\n{entry.link}'
  for url in feed_data['webhook_urls']:
    await post_data_to_webhook(url, json.dumps(announcement))
  msg = await run_friday_scripts()
  info_log(msg)
  info_log(str(len(msg)))
  await channel.send(msg)


async def community_fff_updated(name, feed_data, feed, feeds):
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)
  
  entry = feed.entries[0]
  
  channel = client.get_channel(feed_data['channel'])
  await channel.send(entry.title)
  
  announcement = {}
  announcement['content'] = f'{entry.title}\n<{entry.link}>'
  for url in feed_data['webhook_urls']:
    await post_data_to_webhook(url, json.dumps(announcement))


async def wiki_updated(name, feed_data, feed, feeds):
  time_latest_entry = feed_data['time_latest_entry']
  for i, entry in enumerate(feed.entries):
    if get_formatted_time(entry) > time_latest_entry:
      info_log('Found new wiki entry made on ' + entry.updated)
      summary = ''
      if re.search('<p.*?>.*?<\/p>', entry.summary):
        summary = html.unescape(tomd.convert(re.search('<p.*?>.*?<\/p>', entry.summary).group()))
        summary = re.sub(r'\((\/\S*)\)', r'(https://wiki.factorio.com\1)', summary)
        summary = re.sub('<bdi>|<\/bdi>', '', summary)
      embed = discord.Embed(title = f'{entry.author} changed {entry.title}', color = 14103594, timestamp = datetime.datetime(*entry.updated_parsed[0:6]), url = entry.link, description = summary)
      channel = client.get_channel(feed_data['channel'])
      await channel.send(embed=embed)
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
      if not is_new_version or 'Friday Facts' in entry.title:
        continue
      else:
        version = is_new_version.group(1)
        reddit_url = feed_data['reddit_rss']
        reddit_entry = await get_version_entry_from_reddit(entry.title, reddit_url, 0)
        channel = client.get_channel(feed_data['channel'])
        if not reddit_entry:
          embed = discord.Embed(title = f'Version {version} is out but the reddit post could not be found.', color = 0xff0000, timestamp = datetime.datetime(*entry.updated_parsed[0:6]), url = entry.link)
          await channel.send('<@204512563197640704>', embed=embed)
        
        forum_post_number = re.search('^https:\/\/forums\.factorio\.com\/viewtopic\.php\?t=(\d+)', entry.link).group(1)
        announcement_msg = f'Version {version} released:\n<https://forums.factorio.com/{forum_post_number}>' + f'\n<{reddit_entry.link}>' if reddit_entry else ''
        
        info_log(announcement_msg)
        announcement = {}
        announcement['content'] = announcement_msg
        await channel.send(version)
        for url in feed_data['webhook_urls']:
          await post_data_to_webhook(url, json.dumps(announcement))
        wiki_msg = wiki_new_version(forum_post_number, version)
        await channel.send(wiki_msg)
    else:
      break
  feeds[name]['time_latest_entry'] = get_formatted_time(feed.entries[0])
  with open('feeds.json', 'w') as f:
    json.dump(feeds, f)


async def get_version_entry_from_reddit(entry_title, reddit_url, iteration):
  reddit_feed = await loop.run_in_executor(None, feedparser.parse, reddit_url)
  for i, entry in enumerate(reddit_feed.entries[:5]):
    if entry.title == entry_title:
      return entry
  #couldn't find new version on reddit
  if iteration == 8-1:
    error_log(f'Could not find reddit post for {entry_title} within 8 * 15 seconds. Aborting.')
    return False
  await asyncio.sleep(15)
  await get_version_entry_from_reddit(entry_title, reddit_url, iteration+1)


async def post_data_to_webhook(webhook_url, data):
  result = requests.post(webhook_url, data=data, headers={'Content-Type': 'application/json'})
  try:
    result.raise_for_status()
  except requests.exceptions.HTTPError as err:
    error_log(str(err))


def get_formatted_time(entry):
  return time.strftime('%Y-%m-%dT%H:%M:%S+00:00', entry.updated_parsed)


@client.event
async def on_message(message):
  if message.author.bot:
    return
  
  if message.content.startswith('.ping'):
    msg = f'Hello {message.author.mention}'
    await message.channel.send(msg)
  elif message.content.startswith('.wiki_status'):
    embed = await get_wiki_stats()
    await message.channel.send(embed=embed)
  elif message.content.startswith('.friday') and message.author.id == 204512563197640704:
    info_log('Running Friday scripts')
    msg = await run_friday_scripts()
    info_log(msg)
    info_log(str(len(msg)))
    await message.channel.send(msg)
  elif message.content.startswith('.wanted_pages'):
    if WIKI_EDITOR_ROLE_ID not in [role.id for role in message.author.roles]:
      await message.channel.send('You may not run this command.')
      return
    info_log('Running wanted pages script')
    await message.channel.send('Running script, please be patient')
    msg = await loop.run_in_executor(None, wiki_wanted_pages, False)
    output = '\n'.join([pretty_edit_response(line) for line in msg])
    info_log(output)
    info_log(str(len(output)))
    await message.channel.send(output)
  elif message.content.startswith('.redirects'):
    if WIKI_EDITOR_ROLE_ID not in [role.id for role in message.author.roles]:
      await message.channel.send('You may not run this command.')
      return
    info_log('Running redirects script')
    await message.channel.send('Running script, please be patient')
    msg = await loop.run_in_executor(None, wiki_redirects)
    await message.channel.send(pretty_edit_response(msg))
  elif message.content.startswith('.help') or message.content.startswith('.info'):
    msg = 'Hello, I am Bilka\'s bot. Commands:\n`.help` or `.info` - Prints this message\n`.ping` - Pings this bot\n`.wiki_status` - Prints the current status of wiki.factorio.com'
    if message.guild and WIKI_EDITOR_ROLE_ID in [role.id for role in message.guild.roles]:
      msg += '\nCommands for trusted wiki editors only:'
      msg += '\n`.wanted_pages` - Runs the wanted pages script on wiki.factorio.com\n`.redirects` - Runs the redirects script on wiki.factorio.com'
    msg+='\nSource code: <https://github.com/Bilka2/BilkaBot>'
    await message.channel.send(msg)
    

async def get_wiki_stats():
  session = requests.Session()
  session.params={
    'format': 'json',
    'action': 'query',
    'meta': 'siteinfo',
    'siprop': 'statistics'
  }
  info = await loop.run_in_executor(None, session.get, 'https://wiki.factorio.com/api.php')
  info = info.json()['query']['statistics']
  embed = discord.Embed(color = 14103594, timestamp = datetime.datetime.utcnow())
  for name, value in info.items():
    if name != 'activeusers' and name != 'admins':
      embed.add_field(name = name.capitalize(), value = value)
  return embed


async def run_friday_scripts():
  msg = []
  msg.append(await loop.run_in_executor(None, wiki_analytics))
  msg.append(await loop.run_in_executor(None, wiki_new_fff))
  msg.append(await loop.run_in_executor(None, wiki_redirects))
  msg.extend(await loop.run_in_executor(None, wiki_wanted_pages, False))
  msg = '\n'.join([pretty_edit_response(line) for line in msg])
  return msg


def pretty_edit_response(response):
  if not re.search('title":"([^"]+)"', response) or not re.search('result":"([^"]+)"', response):
    return response
  title = re.search('title":"([^"]+)"', response).group(1)
  result = re.search('result":"([^"]+)"', response).group(1)
  ret = f'Edited {title}: {result}'
  if '"nochange"' in response:
    ret += ', nochange'
  return ret


@client.event
async def on_ready():
  info_log('Logged in as')
  info_log(client.user.name)
  info_log('------')


def error_log(msg):
  print(time.asctime() + ' ' + msg)
  try:
    logging.error(msg)
  except:
    print(time.asctime() + ' Error logging failed.')


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
finally:
  loop.close()
