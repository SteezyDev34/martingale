@echo off
wsl -d Ubuntu-24.04 -- bash -c "cd '/mnt/c/Users/Administrator/Projets/MARTINGAL' && git pull && venv_wsl/bin/pip install -r requirements.txt && venv_wsl/bin/python dashboard.py"
