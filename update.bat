@echo off
echo === Updating HealthyfiedAutomator ===

REM Check if git is available
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: git is not installed. Please install git to use this update script.
    exit /b 1
)

REM Check if we're in a git repository
if not exist ".git" (
    echo Error: This doesn't appear to be a git repository.
    exit /b 1
)

REM Pull the latest changes
echo Pulling latest changes from GitHub...
git pull

REM Check if Python virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating one...
    python -m venv venv
)

REM Activate virtual environment and update dependencies
echo Updating dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo === Update Complete ===
echo Check CURRENT_STATE.md for the latest processing state.
echo.
echo To continue publishing recipes:
echo   cd ghost
echo   python publish_all_recipes.py

pause 