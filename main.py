import discord
import json

with open('config.json', 'r') as f:
  config = json.load(f)

if config['token'] == '':
  print('No token.')

TOKEN = config['token']

client = discord.Client()

@client.event
async def on_message(message):
  # dont reply to bots
  if message.author.bot:
    return
  
  if message.content.startswith('!hello'):
    msg = 'Hello {0.author.mention}'.format(message)
    await client.send_message(message.channel, msg)

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(client.user.id)
  print('------')

client.run(TOKEN)
