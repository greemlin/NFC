# NFC Card Reader Application

A simple cross-platform application to read payment cards using an ACR122U NFC reader.

## Features
- Detects Visa and Mastercard payment cards
- Displays card brand logo
- Shows cardholder name when available
- Real-time card detection
- Simple, clean interface

## Windows Installation Guide

### Prerequisites
1. Install Python 3.8 or newer from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. Install the ACR122U Driver:
   - Download the driver from [ACS Website](https://www.acs.com.hk/en/driver/3/acr122u-usb-nfc-reader/)
   - Run the installer (ACR122U_Driver_Installer.exe)
   - Restart your computer

3. Install the PC/SC Service:
   - The service is included with Windows
   - Ensure "Smart Card" service is running:
     1. Press Win+R
     2. Type "services.msc"
     3. Find "Smart Card" service
     4. Set startup type to "Automatic"
     5. Start the service

### Application Installation

1. Download and extract the application zip file

2. Open Command Prompt as Administrator:
   ```cmd
   Win + X -> Windows Terminal (Admin)
   ```

3. Navigate to the application directory:
   ```cmd
   cd path\to\card_reader_app
   ```

4. Create a virtual environment (recommended):
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

5. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

## Running the Application

1. Connect your ACR122U reader to a USB port

2. Open Command Prompt in the application directory:
   ```cmd
   cd path\to\card_reader_app
   ```

3. Activate virtual environment (if used):
   ```cmd
   venv\Scripts\activate
   ```

4. Run the application:
   ```cmd
   python card_reader.py
   ```

## Troubleshooting

1. "No smart card reader found"
   - Unplug and replug the reader
   - Check if the Smart Card service is running
   - Verify the ACR122U driver is installed
   - Try a different USB port

2. "Failed to connect to card"
   - Make sure the card is placed correctly on the reader
   - Keep the card steady on the reader
   - Try cleaning the card's chip
   - Try with a different card

3. "pyscard not installed"
   - Run `pip install -r requirements.txt` again
   - If error persists, try: `pip install pyscard --no-cache-dir`

## Support

For issues related to:
- ACR122U reader: Contact ACS support
- Application bugs: Open an issue on GitHub
- Installation problems: Check troubleshooting guide above

## Notes
- The application works with EMV payment cards (credit/debit cards)
- Only reads basic card information (no sensitive data)
- Tested with ACR122U reader on Windows 10/11
