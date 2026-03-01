#!/bin/bash
echo "🚀 Starting CareerSync AI Server..."
source .venv/bin/activate
export DASHSCOPE_API_KEY='sk-793fc8d73dac4eaab0be9e2bbbd0433d'
lsof -ti:8443 | xargs kill -9
python3 app.py
