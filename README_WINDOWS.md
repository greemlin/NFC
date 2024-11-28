# EMV Card Reader - Windows Installation Guide

This guide will help you set up and run the EMV Card Reader application on Windows 10/11.

## Prerequisites

1. **Python 3.6 -  3.9 (preferred)
   - Download from [Python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - Verify installation by opening Command Prompt and typing:
     ```
     python --version
     ```

2. **ACR122U NFC Reader**
   - Install the official drivers:
     1. Download "ACR122U USB NFC Reader Driver" from [ACS Website](https://www.acs.com.hk/en/driver/3/acr122u-usb-nfc-reader/)
     2. Extract and run the installer
     3. Restart your computer
   - Verify installation:
     1. Plug in your ACR122U reader
     2. Open Device Manager
     3. Look for "Microsoft USBCCID Smartcard Reader (ACR122U)" under "Smart card readers"

## Installation Steps

1. **Download the Project**
   ```
   git clone https://github.com/greemlin/NFC.git
   cd NFC
   ```

2. **Create Virtual Environment** (Recommended)
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Required Packages**
   ```
   pip install -r requirements.txt
   ```
   If requirements.txt is missing, install these packages:
   ```
   pip install pyscard
   pip install PyQt6
   ```

4. **Install Windows-specific Dependencies**
   - Download and install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - This is required for the pyscard library to work properly

## Running the Application

1. **Connect ACR122U Reader**
   - Plug in your ACR122U NFC reader
   - Wait for Windows to recognize the device (you should hear the USB connection sound)

2. **Start the Application**
   - With virtual environment activated:
     ```
     python card_reader_app/card_reader.py
     ```

## Troubleshooting

### Common Issues and Solutions

1. **"Smart card resource manager has stopped" Error**
   - Open Services (Win + R, type "services.msc")
   - Find "Smart Card" service
   - Right-click → Restart
   - Also restart "Smart Card Device Enumeration Service"

2. **Reader Not Detected**
   - Unplug and replug the reader
   - Try a different USB port
   - Check Device Manager for errors
   - Reinstall ACR122U drivers

3. **"No module named 'smartcard'" Error**
   - Ensure you're in the virtual environment
   - Reinstall pyscard:
     ```
     pip uninstall pyscard
     pip install pyscard
     ```

4. **"No module named 'PyQt6'" Error**
   - Reinstall PyQt6:
     ```
     pip uninstall PyQt6
     pip install PyQt6
     ```

5. **Card Not Reading**
   - Clean the reader with a card cleaning kit
   - Try multiple cards to isolate the issue
   - Check if the card is EMV-compatible

### Advanced Troubleshooting

1. **Check Smart Card Services**
   ```
   sc query scardsvr
   ```

2. **View USB Device Details**
   - Open PowerShell as Administrator
   ```powershell
   Get-PnpDevice | Where-Object {$_.FriendlyName -like "*ACR122*"}
   ```

3. **Enable Debug Logging**
   - Create environment variable:
   ```
   set PYSCARD_DEBUG=1
   ```
   - Run the application to see detailed logs

## Support

If you encounter any issues:
1. Check the Troubleshooting section above
2. Look for error messages in the application window
3. Create an issue on the GitHub repository with:
   - Windows version
   - Python version
   - Error message
   - Steps to reproduce

## Additional Resources

- [ACR122U SDK Documentation](https://www.acs.com.hk/download-manual/419/API-ACR122U-2.04.pdf)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Python Smart Card Library Documentation](https://pyscard.sourceforge.io/user-guide.html)
