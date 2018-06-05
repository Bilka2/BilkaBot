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

Dependencies:
Python 3.6.4+
* feedparser
* discord.py
* tomd
* requests
* local clone of https://github.com/Bilka2/Wiki-scripts
  * requests
