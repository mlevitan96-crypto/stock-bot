#!/bin/bash
cd ~/stock-bot
source venv/bin/activate
python3 check_workflow_audit.py 2>&1
