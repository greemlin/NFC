#!/bin/bash

echo "Building Card Reader Application..."
echo

# Create the icon first
python3 create_icon.py

# Build the executable with wine
python3 -m PyInstaller --clean build.spec

echo
echo "Build complete! The executable can be found in the 'dist' folder."
