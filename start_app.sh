#!/bin/bash
export PYTHONPATH=.
python3 app.py &
APP_PID=$!
echo $APP_PID > app.pid
echo "App started with PID $APP_PID"
sleep 5
