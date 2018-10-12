#!/bin/bash

# Copy watcher.service in /lib/systemd/system to create a service
# commands : sudo systemctl start/stop/restart/status watcher
# if service is started, and the watcher is edited,
# use : sudo systemctl daemon-reload
sudo systemctl stop watcher
sudo cp watcher.service /lib/systemd/system/watcher.service
sudo systemctl daemon-reload
chmod +x watcher
chmod +x log
chmod +x log_error
chmod +x reload_watcher
if [ ! -e /tmp/watcher.log ]
then
  touch /tmp/watcher.log
fi
if [ ! -e /tmp/watcher_error.log ]
then
  touch /tmp/watcher_error.log
fi
sudo systemctl start watcher
sudo systemctl status watcher
tail -f /tmp/watcher.log
