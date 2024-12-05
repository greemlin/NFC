@echo off
echo Building Card Reader Application...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Install requirements
pip install -r requirements.txt

REM Build the executable
pyinstaller --clean build.spec

echo.
echo Build complete! The executable can be found in the "dist" folder.
pause
