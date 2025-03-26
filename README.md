# BilkaBot

A discord bot, used to dispatch wiki scripts when RSS feeds update, or on command.

config.json needs to be added and should look like this:
```json
{
  "token": "<base64 encoded token>",
  "path_to_wiki_scripts": "<path to your local clone of https://github.com/Bilka2/Wiki-scripts>"
}
```

Encoding the token:
```python
import base64
print(base64.b64encode('<TOKEN>'.encode('utf8')).decode('utf8'))
```

feeds.json:
```json
{
"fff":
  {"url": "https://www.factorio.com/blog/rss",
  "channel": <id>,
  "time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
  "sleep_for": 60,
  "webhook_urls": ["<url>", "<url>"]},
"wiki":
  {"url": "https://wiki.factorio.com/api.php?days=14&limit=50&action=feedrecentchanges&feedformat=rss&hidebots=1",
  "channel": <id>,
  "time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
  "sleep_for": 180},
"forums_news":
  {"url": "https://forums.factorio.com/app.php/feed/news",
  "channel": <id>,
  "time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
  "sleep_for": 60,
  "webhook_urls": ["<url>", "<url>"]},
"factorio_versions":
  {"url": "https://factorio.com/api/latest-releases",
  "channel": <id>,
  "latest_stable": "2.0.xx",
  "sleep_for": 180,
  "webhook_urls": ["<url>", "<url>"]}
}
```

Dependencies:
Python 3.8+
* feedparser
* discord.py 2.0+
* tomd
* requests
* local clone of https://github.com/Bilka2/Wiki-scripts
* (May need the `python3-venv` package installed on Debian for creating the virtualenv)

Virtualenv setup:
```
#pwd should be ~
python3 -m venv wiki_bot_env
source wiki_bot_env/bin/activate
python3 --version # needs to be 3.8 or higher
python3 -m pip install -r BilkaBot/dependencies.txt
deactivate
bash BilkaBot/easy-update.sh # start bot, as usual
```
