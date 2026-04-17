@echo off
setlocal

cd /d D:\CODES\project\micro_project\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
