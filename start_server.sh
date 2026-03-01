#!/bin/bash
echo "🚀 Starting CareerSync AI Server..."
source .venv/bin/activate
export DASHSCOPE_API_KEY='sk-93bd6f5cb9b446cc8d64705d96666dd1'
lsof -ti:8443 | xargs kill -9
python3 app.py
