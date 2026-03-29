@echo off
setlocal
if "%~1"=="" (
  echo Usage: run set_ngrok_token.bat YOUR_NGROK_AUTHTOKEN
  exit /b 1
)
D:\CODES\project\micro_project\tools\ngrok\ngrok.exe config add-authtoken %1
