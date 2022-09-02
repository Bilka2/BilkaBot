#!/usr/bin/env bash
# run from home directory
# may need to set this to be executable: chmod +x start.sh
source wiki_bot_env/bin/activate; cd BilkaBot/; python3 main.py; deactivate;
