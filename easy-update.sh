#!/usr/bin/env bash
sudo systemctl stop BilkaBot;
cd ~/Wiki-scripts/;
git pull origin master;
cd ~/BilkaBot/;
git pull origin master;
cd ~;
sudo systemctl start BilkaBot
