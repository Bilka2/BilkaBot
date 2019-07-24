#!/usr/bin/env bash
systemctl stop BilkaBot;
cd ~/Wiki-scripts/;
git pull origin master;
cd ~/BilkaBot/;
git pull origin master;
cd ~;
systemctl start BilkaBot
