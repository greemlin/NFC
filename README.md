# EMV Card Reader

A Python-based EMV (Europay, Mastercard, and Visa) card reader application using the ACR122U NFC reader. This application provides detailed parsing and analysis of EMV card data with a user-friendly GUI interface.

## Features

- Comprehensive EMV tag parsing and decoding
- Support for nested EMV data structures
- Detailed card data analysis
- User-friendly PyQt6-based interface
- Support for ACR122U NFC reader
- Extensive EMV tag dictionary with 150+ tags

## Installation

### Windows Users
Please see [README_WINDOWS.md](README_WINDOWS.md) for detailed Windows installation instructions.

### Linux/Unix Users
1. Install dependencies:
   ```bash
   sudo apt-get install pcscd pcsc-tools python3-pyscard
   ```

2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Connect your ACR122U NFC reader
2. Run the application:
   ```bash
   python card_reader_app/card_reader.py
   ```
3. Place an EMV card on the reader
4. View detailed card information in the application window

## Supported Tags

The application supports a comprehensive list of EMV tags including:
- Basic EMV Tags (Application Data, Card Holder Info)
- Processing Tags
- Template Related Tags
- Security and Verification Tags
- Card Scheme Specific Tags
- And many more...

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- EMV Tag specifications from [EMV® Book 3](https://www.emvco.com/specifications/)
- ACR122U documentation from [Advanced Card Systems Ltd.](https://www.acs.com.hk/)
