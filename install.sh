#!/bin/sh

if [ ! -f /etc/servemp3.config ]; then
  printf "Copying servemp3.config to /etc... "
  sudo cp ./servemp3.config /etc/servemp3.config
  printf "done\n"
else
  printf "\n\nConfiguration file found, skipping installation to /etc\n\n"
fi

printf "Copying servemp3.py to /usr/local/bin... "
sudo cp ./servemp3.py /usr/local/bin/servemp3.py
printf "done\n"

printf "Copying encoding directory module to /usr/local/bin..."
sudo cp -R ./encoding /usr/local/bin
printf "done\n"

if [ -f /etc/systemd/system/servemp3.service ]; then
  printf "Stopping and disabling systemd service...\n"
  sudo systemctl stop servemp3
  sudo systemctl disable servemp3
  printf "  done\n"
fi

printf "Copying servemp3.service to /etc/systemd/system... "
sudo cp ./servemp3.service /etc/systemd/system/servemp3.service
printf "done\n"

printf "Enabling systemd service... "
cd /etc/systemd/system && sudo systemctl enable servemp3
printf "done\n"

printf "Starting servemp3 service...\n"
sudo systemctl start servemp3
printf "  done\n"
