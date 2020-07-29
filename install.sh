#!/bin/sh

printf "Copying servemp3.config to /etc... "
sudo cp ./servemp3.config /etc/servemp3.config
printf "done\n"

printf "Copying servemp3.py to /usr/local/bin... "
sudo cp ./servemp3.py /usr/local/bin/servemp3.py
printf "done\n"

printf "Copying encoding directory module to /usr/local/bin..."
sudo cp -R ./encoding /usr/local/bin/encoding
printf "done\n"

printf "Copying servemp3.service to /etc/systemd/system... "
sudo cp ./servemp3.service /etc/systemd/system/servemp3.service
printf "done\n"

printf "Enabling systemd service... "
cd /etc/systemd/system && sudo systemctl enable servemp3
printf "done\n"
