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
	"channel": "<id>",
	"time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
	"sleep_for": 60,
  "webhook_urls": ["<url>", "<url>"]},
"wiki":
	{"url": "https://wiki.factorio.com/api.php?days=14&limit=50&action=feedrecentchanges&feedformat=rss&hidebots=1",
	"channel": "<id>",
	"time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
	"sleep_for": 180},
"forums_news":
	{"url": "https://forums.factorio.com/app.php/feed/news",
	"channel": "<id>",
	"time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
	"sleep_for": 60,
	"reddit_rss": "https://www.reddit.com/user/FactorioTeam/.rss",
	"webhook_urls": ["<url>", "<url>"]}
},
"subreddit":
	{"url": "https://www.reddit.com/r/technicalfactorio/new.rss",
	"channel": "<id>",
	"time_latest_entry": "<time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time)>",
	"sleep_for": 180}
}
```

Dependencies:
Python 3.6.4+
* feedparser
* discord.py
* tomd
* requests
* beautifulsoup4
* local clone of https://github.com/Bilka2/Wiki-scripts
