import discord
import json
import base64
import sys

with open('config.json', 'r') as f:
  config = json.load(f)

sys.path.append(config['path_to_wiki_scripts'])
from analytics import main as wiki_analytics
from new_fff import main as wiki_new_fff

if config['token'] == '':
  print('No token.')

TOKEN = base64.b64decode(config['token']).decode('utf-8')

client = discord.Client()

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
  print(client.user.id)
  print('------')

client.run(TOKEN)
