@echo off
REM ============================================================
REM  CraveSave bot launcher for Windows
REM  1. Replace the 4 values below with your real keys
REM  2. Save this file
REM  3. Double-click it to run the bot
REM  KEEP THIS FILE ON YOUR PC ONLY - it holds your secret token.
REM  Do NOT upload it to your public GitHub repo.
REM ============================================================

set AMZN_TAG=yourtag-21
set TG_BOT_TOKEN=123456:ABC-your-token-here
set TG_CHANNEL=@YourChannel
set TG_OWNER_ID=your_numeric_id

python telegram_bot.py

echo.
echo Bot stopped. Press any key to close.
pause >nul
