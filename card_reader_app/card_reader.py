import sys
import os
import threading
import time
import queue
import logging

from PyQt6.QtCore import Qt, QTimer, QSize, QMetaObject, Q_ARG
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QSizePolicy, QDialog, QTextEdit
)
from PyQt6.QtMultimedia import (
    QMediaDevices, QCamera, QMediaCaptureSession,
    QVideoSink, QVideoFrame, QImageCapture
)
from PyQt6.QtMultimediaWidgets import QVideoWidget

from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException, CardConnectionException
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# EMV Tag Definitions
EMV_TAGS = {
    # Template Tags
    '6F': 'File Control Information (FCI) Template',
    '70': 'Record Template',
    '77': 'Response Message Template Format 2',
    '80': 'Response Message Template Format 1',
    '84': 'Dedicated File (DF) Name',
    'A5': 'File Control Information (FCI) Proprietary Template',
    '61': 'Application Template',
    
    # Basic Data Elements
    '42': 'Issuer Identification Number (IIN)',
    '4F': 'Application Identifier (AID)',
    '50': 'Application Label',
    '56': 'Track 1 Equivalent Data (Magnetic Stripe Data)',
    '57': 'Track 2 Equivalent Data',
    '5A': 'Application Primary Account Number (PAN)',
    '5F20': 'Cardholder Name',
    '5F24': 'Application Expiration Date',
    '5F25': 'Application Effective Date',
    '5F28': 'Issuer Country Code',
    '5F2A': 'Transaction Currency Code',
    '5F2D': 'Language Preference',
    '5F30': 'Service Code',
    '5F34': 'Application PAN Sequence Number',
    '5F36': 'Transaction Currency Exponent',
    
    # Processing Tags
    '82': 'Application Interchange Profile',
    '83': 'Command Template',
    '86': 'Issuer Script Command',
    '87': 'Application Priority Indicator',
    '88': 'Short File Identifier (SFI)',
    '89': 'Authorization Code',
    '8A': 'Authorization Response Code',
    '8C': 'Card Risk Management Data Object List 1 (CDOL1)',
    '8D': 'Card Risk Management Data Object List 2 (CDOL2)',
    '8E': 'Cardholder Verification Method (CVM) List',
    '8F': 'Certification Authority Public Key Index',
    '90': 'Issuer Public Key Certificate',
    '91': 'Issuer Authentication Data',
    '92': 'Issuer Public Key Remainder',
    '93': 'Signed Static Application Data',
    '94': 'Application File Locator (AFL)',
    '95': 'Terminal Verification Results',
    '97': 'Transaction Certificate Data Object List (TDOL)',
    '98': 'Transaction Certificate (TC) Hash Value',
    '99': 'Transaction Personal Identification Number (PIN) Data',
    '9A': 'Transaction Date',
    '9B': 'Transaction Status Information',
    '9C': 'Transaction Type',
    '9D': 'Directory Definition File (DDF) Name',
    
    # 9F Series Tags
    '9F01': 'Acquirer Identifier',
    '9F02': 'Amount, Authorized (Numeric)',
    '9F03': 'Amount, Other (Numeric)',
    '9F04': 'Amount, Other (Binary)',
    '9F05': 'Application Discretionary Data',
    '9F06': 'Application Identifier (AID) - Terminal',
    '9F07': 'Application Usage Control',
    '9F08': 'Application Version Number',
    '9F09': 'Application Version Number - Terminal',
    '9F0B': 'Cardholder Name Extended',
    '9F0D': 'Issuer Action Code - Default',
    '9F0E': 'Issuer Action Code - Denial',
    '9F0F': 'Issuer Action Code - Online',
    '9F10': 'Issuer Application Data',
    '9F11': 'Issuer Code Table Index',
    '9F12': 'Application Preferred Name',
    '9F13': 'Last Online Application Transaction Counter (ATC) Register',
    '9F14': 'Lower Consecutive Offline Limit',
    '9F15': 'Merchant Category Code',
    '9F16': 'Merchant Identifier',
    '9F17': 'Personal Identification Number (PIN) Try Counter',
    '9F18': 'Issuer Script Identifier',
    '9F1A': 'Terminal Country Code',
    '9F1B': 'Terminal Floor Limit',
    '9F1C': 'Terminal Identification',
    '9F1D': 'Terminal Risk Management Data',
    '9F1E': 'Interface Device (IFD) Serial Number',
    '9F1F': 'Track 1 Discretionary Data',
    '9F20': 'Track 2 Discretionary Data',
    '9F21': 'Transaction Time',
    '9F22': 'Certification Authority Public Key Index - Terminal',
    '9F23': 'Upper Consecutive Offline Limit',
    '9F26': 'Application Cryptogram',
    '9F27': 'Cryptogram Information Data',
    '9F2D': 'ICC PIN Encipherment Public Key Certificate',
    '9F2E': 'ICC PIN Encipherment Public Key Exponent',
    '9F2F': 'ICC PIN Encipherment Public Key Remainder',
    '9F32': 'Issuer Public Key Exponent',
    '9F33': 'Terminal Capabilities',
    '9F34': 'Cardholder Verification Method (CVM) Results',
    '9F35': 'Terminal Type',
    '9F36': 'Application Transaction Counter (ATC)',
    '9F37': 'Unpredictable Number',
    '9F38': 'Processing Options Data Object List (PDOL)',
    '9F39': 'Point-of-Service (POS) Entry Mode',
    '9F3A': 'Amount, Reference Currency',
    '9F3B': 'Application Reference Currency',
    '9F3C': 'Transaction Reference Currency Code',
    '9F3D': 'Transaction Reference Currency Exponent',
    '9F40': 'Additional Terminal Capabilities',
    '9F41': 'Transaction Sequence Counter',
    '9F42': 'Application Currency Code',
    '9F43': 'Application Reference Currency Exponent',
    '9F44': 'Application Currency Exponent',
    '9F45': 'Data Authentication Code',
    '9F46': 'ICC Public Key Certificate',
    '9F47': 'ICC Public Key Exponent',
    '9F48': 'ICC Public Key Remainder',
    '9F49': 'Dynamic Data Authentication Data Object List (DDOL)',
    '9F4A': 'Static Data Authentication Tag List',
    '9F4B': 'Signed Dynamic Application Data',
    '9F4C': 'ICC Dynamic Number',
    '9F4D': 'Log Entry',
    '9F4E': 'Merchant Name and Location',
    '9F4F': 'Log Format',
    '9F50': 'Offline Accumulator Balance',
    '9F51': 'DRDOL Related Data',
    '9F52': 'Terminal Compatibility Indicator',
    '9F53': 'Consecutive Transaction Limit (International)',
    '9F54': 'Cumulative Total Transaction Amount Limit',
    '9F55': 'Geographic Indicator',
    '9F56': 'Issuer Authentication Indicator',
    '9F57': 'Issuer Country Code',
    '9F58': 'Lower Consecutive Offline Limit (International)',
    '9F59': 'Upper Consecutive Offline Limit (International)',
    '9F5A': 'Issuer URL2',
    '9F5B': 'Issuer Script Results',
    '9F5C': 'Upper Cumulative Total Transaction Amount Limit',
    '9F66': 'Terminal Transaction Qualifiers (TTQ)',
    '9F6B': 'Track 2 Equivalent Data (Magnetic Stripe Data)',
    '9F6C': 'Card Transaction Qualifiers (CTQ)',
    '9F6E': 'Form Factor Indicator',
    '9F72': 'Consecutive Transaction International Upper Limit',
    '9F73': 'Currency Conversion Factor',
    '9F74': 'VLP Issuer Authorization Code',
    '9F75': 'Cumulative Total Transaction Amount Upper Limit',
    '9F76': 'Secondary Application Currency Code',
    '9F77': 'VLP Funds Limit',
    '9F78': 'VLP Single Transaction Limit',
    '9F79': 'VLP Available Funds',
    '9F7A': 'VLP Single Transaction Limit',
    '9F7B': 'VLP Transaction Qualifier',
    '9F7C': 'Customer Exclusive Data',
    '9F7D': 'Application Specific Transparent Template',
    
    # BF Series Tags
    'BF0C': 'File Control Information (FCI) Issuer Discretionary Data',
    
    # Card Scheme Specific
    'DF8104': 'Balance Read Before Gen AC',
    'DF8105': 'Balance Read After Gen AC',
    'DF8106': 'Data Needed',
    'DF8107': 'CDOL1 Related Data',
    'DF8108': 'DS AC Type',
    'DF8109': 'DS Input (Term)',
    'DF810A': 'DS ODS Info',
    'DF810B': 'DS Summary 1',
    'DF810C': 'DS Summary 2',
    'DF810D': 'DS Summary 3',
    'DF810E': 'DS Unpredictable Number',
    'DF810F': 'Message Hold Time',
    'DF8110': 'Phone Message Table',
    'DF8111': 'Phone Response Code',
    'DF8112': 'Script Hold Time',
    'DF8113': 'Issuer Script Results',
    'DF8114': 'Post-Gen AC Put Data Status',
    'DF8115': 'Pre-Gen AC Put Data Status',
    'DF8116': 'Proceed To First Write Flag',
    'DF8117': 'PDOL Related Data',
    'DF8118': 'Tags To Read',
    'DF8119': 'Tags To Write Before Gen AC',
    'DF811A': 'Tags To Write After Gen AC',
    'DF811B': 'Data To Send',
    'DF811C': 'Data Record',
    'DF811D': 'Encryption Key',
    'DF811E': 'Encrypted Data'
}

SELECT_VISA_AID = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x03, 0x10, 0x10]
SELECT_MASTERCARD_AID = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x04, 0x10, 0x10]
GET_PROCESSING_OPTIONS = [0x80, 0xA8, 0x00, 0x00, 0x02, 0x83, 0x00, 0x00]

class CardReader(QWidget):
    def __init__(self):
        super().__init__()
        self.connection = None
        self.reader = None
        self.card_type = None
        self.last_atr = None
        self.camera_widget = None  # Will hold our CameraWidget instance
        self.init_ui()
        self.setup_card_reader()
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_card)
        self.timer.start(1000)  # Poll every second

    def setup_camera(self):
        """Initialize the camera using CameraWidget."""
        try:
            # Create camera widget if not exists
            if not hasattr(self, 'camera_widget'):
                self.camera_widget = CameraWidget()
                self.camera_widget.setParent(self)
                self.camera_container.layout().addWidget(self.camera_widget)
                logger.debug("Camera widget created and added to container")
            
        except Exception as e:
            logger.error(f"Error setting up camera: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Status bar at top
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("QLabel { color: #666; }")
        layout.addWidget(self.status_label)
        
        # Top section with camera and card image
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)  # Add more space between camera and card display
        
        # Camera feed container
        camera_section = QWidget()
        camera_layout = QVBoxLayout(camera_section)
        camera_layout.setSpacing(5)
        
        camera_label = QLabel("Camera Feed")
        camera_label.setStyleSheet("QLabel { color: #666; font-weight: bold; }")
        camera_layout.addWidget(camera_label)
        
        self.camera_container = QWidget()
        self.camera_container.setFixedSize(400, 300)
        self.camera_container.setStyleSheet("QWidget { border: 2px solid #dee2e6; border-radius: 4px; background: #f8f9fa; }")
        camera_container_layout = QHBoxLayout(self.camera_container)
        camera_container_layout.setContentsMargins(0, 0, 0, 0)
        camera_layout.addWidget(self.camera_container)
        
        top_layout.addWidget(camera_section)
        
        # Card image container
        card_section = QWidget()
        card_layout = QVBoxLayout(card_section)
        card_layout.setSpacing(5)
        
        card_label = QLabel("Card Information")
        card_label.setStyleSheet("QLabel { color: #666; font-weight: bold; }")
        card_layout.addWidget(card_label)
        
        card_container = QWidget()
        card_container.setFixedSize(400, 300)
        card_container.setStyleSheet("QWidget { border: 2px solid #dee2e6; border-radius: 4px; background: #f8f9fa; }")
        card_container_layout = QHBoxLayout(card_container)
        card_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.card_image_label = QLabel("Waiting for card...")
        self.card_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_container_layout.addWidget(self.card_image_label)
        card_layout.addWidget(card_container)
        
        top_layout.addWidget(card_section)
        layout.addLayout(top_layout)
        
        # Card data display
        self.card_data_display = CardDataDisplay()
        layout.addWidget(self.card_data_display)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 14px;
            }
            QLabel {
                padding: 5px;
            }
        """)

    def update_card_image(self):
        """Update the card image based on detected card type."""
        if self.card_type == "Visa" and hasattr(self, 'visa_image'):
            pixmap = QPixmap.fromImage(self.visa_image)
        elif self.card_type == "Mastercard" and hasattr(self, 'mastercard_image'):
            pixmap = QPixmap.fromImage(self.mastercard_image)
        else:
            return

        if not pixmap.isNull():
            # Scale the pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.card_image_label.size(), 
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
            self.card_image_label.setPixmap(scaled_pixmap)
            self.card_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def poll_card(self):
        """Poll for card presence and read data if card is present."""
        try:
            connection = self.reader.createConnection()
            if not connection.connect():
                self.connection = None
                self.card_type = None
                self.last_atr = None
                self.status_label.setText("Waiting for card...")
                self.card_image_label.clear()
                self.card_data_display.update_display("No card present")
                return

            # Get ATR
            atr = connection.getATR()
            if atr != self.last_atr:
                logger.debug(f"New card detected with ATR: {' '.join([f'{b:02X}' for b in atr])}")
                self.last_atr = atr
                self.connection = connection

                # Detect card type
                self.card_type = self.detect_card_type(connection)
                if not self.card_type:
                    self.status_label.setText("Unknown card type")
                    self.card_data_display.update_display("Unknown card type")
                    return

                self.status_label.setText(f"{self.card_type} card detected")
                self.update_card_image()

                # Read EMV data
                try:
                    card_data = self.read_card_data(connection, self.card_type)
                    logger.debug(f"Type of card_data: {type(card_data)}")
                    if not isinstance(card_data, dict):
                        logger.error("Card data is not a dictionary")
                        self.card_data_display.update_display(f"Invalid card data format: {str(card_data)}")
                        return

                    if card_data.get('status') != 'success':
                        self.card_data_display.update_display(f"Error reading card: {card_data.get('status', 'Unknown error')}")
                        return

                    # Format the data as a simple string
                    display_text = []
                    display_text.append(f"Card Type: {card_data.get('card_type', 'Unknown')}")
                    display_text.append(f"Status: {card_data.get('status', 'Unknown')}")
                    
                    if card_data.get('atr'):
                        atr_str = ' '.join([f'{b:02X}' for b in card_data['atr']])
                        display_text.append(f"ATR: {atr_str}")

                    if card_data.get('emv_data'):
                        display_text.append("\nEMV Data:")
                        for item in card_data['emv_data']:
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    display_text.append(f"  {k}: {v}")

                    self.card_data_display.update_display('\n'.join(display_text))

                except Exception as e:
                    logger.error(f"Error processing card data: {str(e)}")
                    self.card_data_display.update_display(f"Error processing card: {str(e)}")

        except Exception as e:
            logger.error(f"Error in card polling: {str(e)}")
            self.connection = None
            self.card_type = None
            self.last_atr = None
            self.status_label.setText("Error reading card")
            self.card_data_display.update_display(f"Error: {str(e)}")

    def setup_card_reader(self):
        """Initialize the card reader."""
        try:
            available_readers = readers()
            if not available_readers:
                logger.error("No readers available")
                self.status_label.setText("No card reader found")
                return

            self.reader = available_readers[0]
            logger.debug(f"Using reader: {self.reader}")
            self.status_label.setText(f"Using reader: {self.reader}")
            
            # Load card type images
            self.visa_image = self.load_card_image("visa.png")
            self.mastercard_image = self.load_card_image("mastercard.png")
            
            # Initialize camera after card reader is set up
            self.setup_camera()
            
        except Exception as e:
            logger.error(f"Error setting up card reader: {str(e)}")
            self.status_label.setText("Error initializing card reader")

    def load_card_image(self, image_name):
        """Load a card type image."""
        try:
            image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", image_name)
            logger.debug(f"Loading {image_name.split('.')[0].title()} image from: {image_path}")
            
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
                
            image = QImage(image_path)
            if image.isNull():
                logger.error(f"Failed to load image: {image_path}")
                return None
                
            logger.debug(f"Loaded {image_name.split('.')[0].title()} image successfully")
            return image
            
        except Exception as e:
            logger.error(f"Error loading {image_name}: {str(e)}")
            return None

    def summarize_card_data(self, card_data):
        """Summarize the card data for display"""
        if not isinstance(card_data, dict):
            return str(card_data)

        summary = []
        
        # Basic Card Information
        if card_data.get('card_type'):
            summary.append(f"Card Type: {card_data['card_type']}")
        
        if card_data.get('status'):
            summary.append(f"Status: {card_data['status']}")
            if card_data['status'] != 'success':
                return '\n'.join(summary)
        
        if card_data.get('atr'):
            atr_bytes = card_data['atr']
            atr_str = ' '.join([f'{b:02X}' for b in atr_bytes])
            summary.append(f"ATR: {atr_str}")

        # Process EMV data if available
        emv_data = card_data.get('emv_data', [])
        if emv_data:
            summary.append("\nEMV Data:")
            for record in emv_data:
                if isinstance(record, dict):
                    for k, v in record.items():
                        summary.append(f"  {k}: {v}")

        return '\n'.join(summary) if summary else "No card data available"

    def format_section(self, title, content):
        """Format a section of card data with a title."""
        if not content:
            return ""
            
        formatted = [f"\n{title}", "=" * len(title)]
        
        if isinstance(content, str):
            formatted.append(content)
        elif isinstance(content, dict):
            for key, value in content.items():
                formatted.append(f"{key}: {value}")
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, str):
                    formatted.append(item)
                elif isinstance(item, dict):
                    for key, value in item.items():
                        formatted.append(f"{key}: {value}")
                else:
                    formatted.append(str(item))
        else:
            formatted.append(str(content))
            
        formatted.append("")  # Add empty line at end
        return "\n".join(formatted)

    def template_tags(self):
        """Return a list of template tags that are containers for other tags."""
        return [
            '6F',  # File Control Information (FCI) Template
            '70',  # Record Template
            '77',  # Response Message Template Format 2
            'A5',  # FCI Proprietary Template
            '61',  # Application Template
            'BF0C', # FCI Issuer Discretionary Data
            'BF20', # FCI Proprietary Template
            '73',   # Directory Discretionary Template
            'BF21'  # Log Entry Template
        ]

    def decode_atr(self, atr):
        """Decode ATR (Answer To Reset) value."""
        try:
            atr_info = []
            atr_bytes = bytes.fromhex(atr.replace(' ', ''))
            
            # Initial character TS
            ts = atr_bytes[0]
            if ts == 0x3B:
                atr_info.append("Direct Convention")
            elif ts == 0x3F:
                atr_info.append("Inverse Convention")
                
            # Format character T0
            t0 = atr_bytes[1]
            y1 = (t0 >> 4) & 0x0F  # Higher 4 bits for interface bytes
            k = t0 & 0x0F          # Lower 4 bits for historical bytes
            
            if y1 & 0x1: atr_info.append("TA1 present")
            if y1 & 0x2: atr_info.append("TB1 present")
            if y1 & 0x4: atr_info.append("TC1 present")
            if y1 & 0x8: atr_info.append("TD1 present")
            
            # Try to decode historical bytes as ASCII
            historical = atr_bytes[-k:] if k > 0 else b''
            try:
                ascii_str = historical.decode('ascii')
                if ascii_str.isprintable():
                    atr_info.append(f"Historical: {ascii_str}")
                else:
                    atr_info.append(f"Historical: {historical.hex().upper()}")
            except:
                if historical:
                    atr_info.append(f"Historical: {historical.hex().upper()}")
            
            return f"{atr} ({' | '.join(atr_info)})"
        except Exception as e:
            logger.error(f"Error decoding ATR: {e}")
            return atr

    def try_decode_unknown(self, value):
        """Try to decode unknown values as string or number."""
        try:
            # Try ASCII first
            try:
                ascii_text = bytes.fromhex(value).decode('ascii')
                if ascii_text.isprintable():
                    return f"ASCII: {ascii_text}"
            except:
                pass
            
            # Try as number if 8 bytes or less
            if len(value) <= 16:
                num = int(value, 16)
                return f"NUM: {num} (0x{value})"
            
            # Format hex in simple groups of 2
            hex_bytes = [value[i:i+2] for i in range(0, len(value), 2)]
            return f"HEX: {' '.join(hex_bytes)}"
                
        except Exception as e:
            logger.error(f"Error in try_decode_unknown: {e}")
            return value

    def decode_emv_value(self, tag, value):
        """Decode EMV value based on tag type with enhanced parsing."""
        try:
            # Check if tag is known or unknown
            is_unknown_tag = tag not in EMV_TAGS
            tag_name = 'Unknown Tag' if is_unknown_tag else EMV_TAGS[tag]
            
            # Application Primary Account Number (PAN)
            if tag in ['5A', '57']:
                pan = value.rstrip('F')
                return f"{tag_name}: {' '.join(pan[i:i+4] for i in range(0, len(pan), 4))}"
            
            # Text fields
            elif tag in ['50', '5F20', '9F12', '5F50']:
                try:
                    text = bytes.fromhex(value).decode('ascii').strip()
                    return f"{tag_name}: {text}"
                except:
                    return f"{tag_name} (Hex): {value}"
            
            # Date fields
            elif tag in ['5F24', '5F25']:
                try:
                    year = value[:2]
                    month = value[2:4]
                    day = value[4:6]
                    return f"{tag_name}: 20{year}-{month}-{day}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Country and currency codes
            elif tag in ['5F28', '5F2A', '9F1A']:
                try:
                    code = int(value, 16)
                    return f"{tag_name}: {code}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Amount fields
            elif tag in ['9F02', '9F03', '9F04', '9F3A']:
                try:
                    amount = int(value, 16)
                    return f"{tag_name}: {amount/100:.2f}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Counter fields
            elif tag in ['9F36', '9F17', '9F41']:
                try:
                    return f"{tag_name}: {int(value, 16)}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Application Usage Control
            elif tag == '9F07':
                services = []
                try:
                    auc = int(value, 16)
                    if auc & 0x80: services.append("ATM")
                    if auc & 0x40: services.append("Non-ATM")
                    if auc & 0x20: services.append("Domestic")
                    if auc & 0x10: services.append("International")
                    return f"{tag_name}: {', '.join(services)}" if services else f"{tag_name} (Raw): {value}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Application Interchange Profile
            elif tag == '82':
                try:
                    aip = int(value, 16)
                    features = []
                    if aip & 0x80: features.append("CDA Supported")
                    if aip & 0x40: features.append("RFU")
                    if aip & 0x20: features.append("EMV Mode")
                    if aip & 0x10: features.append("Terminal Risk Management")
                    if aip & 0x08: features.append("Cardholder Verification")
                    if aip & 0x04: features.append("DDA Supported")
                    if aip & 0x02: features.append("SDA Supported")
                    if aip & 0x01: features.append("RFU")
                    return f"{tag_name}: {', '.join(features)}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Terminal Verification Results
            elif tag == '95':
                try:
                    tvr = int(value, 16)
                    results = []
                    if tvr & 0x8000: results.append("Offline Data Authentication Failed")
                    if tvr & 0x4000: results.append("SDA Failed")
                    if tvr & 0x2000: results.append("ICC Data Missing")
                    if tvr & 0x1000: results.append("Card Appears on Terminal Exception File")
                    if tvr & 0x0800: results.append("DDA Failed")
                    if tvr & 0x0400: results.append("CDA Failed")
                    return f"{tag_name}: {', '.join(results)}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Terminal Capabilities
            elif tag == '9F33':
                try:
                    cap = bytes.fromhex(value)
                    features = []
                    if cap[0] & 0x80: features.append("Manual Key Entry")
                    if cap[0] & 0x40: features.append("Magnetic Stripe")
                    if cap[0] & 0x20: features.append("IC with Contacts")
                    return f"{tag_name}: {', '.join(features)}"
                except:
                    return f"{tag_name} (Raw): {value}"
            
            # Default - return with tag name
            # For unknown tags, include the tag number in parentheses
            if is_unknown_tag:
                return f"Unknown Tag ({tag}): {value}"
            return f"{tag_name}: {value}"
            
        except Exception as e:
            logger.error(f"Error decoding tag {tag}: {str(e)}")
            return f"Error decoding {tag}: {value}"

    def parse_tlv(self, hex_string, level=0):
        """Parse TLV (Tag Length Value) data from hex string."""
        try:
            if not hex_string:
                return {}

            # Convert input to bytes if it's not already
            if isinstance(hex_string, str):
                try:
                    # Try to convert hex string to bytes
                    hex_string = bytes.fromhex(hex_string.replace(' ', ''))
                except ValueError:
                    logger.error(f"Invalid hex string: {hex_string}")
                    return {}
            elif isinstance(hex_string, list):
                hex_string = bytes(hex_string)
            elif not isinstance(hex_string, bytes):
                logger.error(f"Unsupported data type for TLV parsing: {type(hex_string)}")
                return {}

            # Convert bytes to list of integers for processing
            data = list(hex_string)
            
            result = {}
            i = 0
            while i < len(data):
                # Get tag
                if i >= len(data):
                    break
                    
                tag = data[i]
                tag_str = f'{tag:02X}'
                i += 1

                # Check for extended tag
                if (tag & 0x1F) == 0x1F:
                    while i < len(data) and (data[i] & 0x80) == 0x80:
                        tag_str += f'{data[i]:02X}'
                        i += 1
                    if i < len(data):
                        tag_str += f'{data[i]:02X}'
                        i += 1

                # Get length
                if i >= len(data):
                    break
                length = data[i]
                i += 1

                if (length & 0x80) == 0x80:
                    num_bytes = length & 0x7F
                    if i + num_bytes > len(data):
                        break
                    length = 0
                    for j in range(num_bytes):
                        length = (length << 8) | data[i + j]
                    i += num_bytes

                # Get value
                if i + length > len(data):
                    break
                value = data[i:i + length]
                i += length

                # Convert value to hex string
                value_str = ' '.join([f'{b:02X}' for b in value])

                # Try to decode the value based on the tag
                decoded_value = self.decode_emv_value(tag_str, value)
                
                # Store both raw and decoded values
                result[tag_str] = {
                    'raw': value_str,
                    'decoded': decoded_value,
                    'description': EMV_TAGS.get(tag_str, 'Unknown Tag')
                }

            if not result:
                logger.warning("No TLV data parsed")
                
            return result

        except Exception as e:
            logger.error(f"Error parsing TLV data: {str(e)}")
            return {}

    def read_card_data(self, connection, card_type):
        """Read data from the card."""
        try:
            if not connection or not card_type:
                logger.debug("No connection or card type provided.")
                return {
                    'card_type': card_type if card_type else 'unknown',
                    'status': 'error',
                    'message': 'No connection or card type',
                    'atr': None,
                    'emv_data': []
                }

            card_data = {
                'card_type': card_type,
                'status': 'unknown',
                'message': '',
                'atr': connection.getATR(),
                'emv_data': []
            }

            logger.debug(f"Initial card data: {card_data}")

            # Select and read EMV applications
            emv_data = []
            
            # Try Visa AID if it's a Visa card
            if card_type == 'Visa':
                visa_response = self.send_apdu(connection, SELECT_VISA_AID)
                logger.debug(f"Visa response: {visa_response}")
                if isinstance(visa_response, dict) and visa_response.get('success'):
                    parsed_data = self.parse_tlv(visa_response.get('data', []))
                    if parsed_data:
                        emv_data.append({
                            'type': 'Visa FCI',
                            'data': parsed_data
                        })
            
            # Try Mastercard AID if it's a Mastercard
            if card_type == 'Mastercard':
                mc_response = self.send_apdu(connection, SELECT_MASTERCARD_AID)
                logger.debug(f"Mastercard response: {mc_response}")
                if isinstance(mc_response, dict) and mc_response.get('success'):
                    parsed_data = self.parse_tlv(mc_response.get('data', []))
                    if parsed_data:
                        emv_data.append({
                            'type': 'Mastercard FCI',
                            'data': parsed_data
                        })
                    
                    # Get Processing Options
                    gpo_response = self.send_apdu(connection, GET_PROCESSING_OPTIONS)
                    logger.debug(f"GPO response: {gpo_response}")
                    if isinstance(gpo_response, dict) and gpo_response.get('success'):
                        parsed_gpo = self.parse_tlv(gpo_response.get('data', []))
                        if parsed_gpo:
                            emv_data.append({
                                'type': 'Processing Options',
                                'data': parsed_gpo
                            })
                    
                    # Read Records
                    for record in range(1, 3):  # Usually 1-2 records
                        record_response = self.send_apdu(connection, [0x00, 0xB2, record, 0x64, 0x00])
                        logger.debug(f"Record {record} response: {record_response}")
                        if isinstance(record_response, dict) and record_response.get('success'):
                            parsed_record = self.parse_tlv(record_response.get('data', []))
                            if parsed_record:
                                emv_data.append({
                                    'type': f'Record {record}',
                                    'data': parsed_record
                                })

            if emv_data:
                card_data['status'] = 'success'
                card_data['message'] = 'EMV data read successfully'
                card_data['emv_data'] = emv_data
            else:
                card_data['status'] = 'no_emv_data'
                card_data['message'] = 'No EMV data available'

            logger.debug(f"Final card data: {card_data}")
            return card_data

        except Exception as e:
            logger.error(f"Error reading card data: {str(e)}")
            return {
                'card_type': card_type if card_type else 'unknown',
                'status': 'error',
                'message': str(e),
                'atr': None,
                'emv_data': []
            }

    def read_emv_data(self, connection):
        """Read EMV data from the card."""
        try:
            # First detect the card type
            card_type = self.detect_card_type(connection)
            if not card_type:
                logger.error("Could not detect card type")
                return None

            # Read the card data
            emv_data = self.read_card_data(connection, card_type)
            if not isinstance(emv_data, dict):
                logger.error("Invalid card data format")
                return None

            return emv_data

        except Exception as e:
            logger.error(f"Error reading EMV data: {str(e)}", exc_info=True)
            return None

    def detect_card_type(self, connection):
        """Detect if card is Visa or Mastercard."""
        try:
            # Try Visa AID
            response = self.send_apdu(connection, SELECT_VISA_AID)
            if response and response['success']:
                return 'Visa'

            # Try Mastercard AID
            response = self.send_apdu(connection, SELECT_MASTERCARD_AID)
            if response and response['success']:
                return 'Mastercard'

            return 'Unknown'
        except Exception as e:
            logger.error(f"Error detecting card type: {str(e)}")
            return 'Unknown'

    def send_apdu(self, connection, apdu):
        """Send APDU command to card and return response."""
        try:
            response, sw1, sw2 = connection.transmit(apdu)
            
            # Log the APDU command and response for debugging
            apdu_hex = ' '.join([f'{b:02X}' for b in apdu])
            resp_hex = ' '.join([f'{b:02X}' for b in response]) if response else 'None'
            logger.debug(f"APDU Command: {apdu_hex}")
            logger.debug(f"Response: {resp_hex}, SW1: {sw1:02X}, SW2: {sw2:02X}")
            
            # Create a response object
            result = {
                'data': response if response else None,
                'sw1': sw1,
                'sw2': sw2,
                'success': sw1 == 0x90 or sw1 == 0x61
            }
            
            # Log any error conditions
            if not result['success']:
                if sw1 == 0x6A:
                    if sw2 == 0x82:
                        logger.error("File or application not found")
                    elif sw2 == 0x86:
                        logger.error("Incorrect parameters P1-P2")
                    elif sw2 == 0x81:
                        logger.error("Function not supported")
                    else:
                        logger.error(f"Command failed with SW1=6A, SW2={sw2:02X}")
                elif sw1 == 0x6D:
                    logger.error("Instruction code not supported")
                elif sw1 == 0x6E:
                    logger.error("Class not supported")
                elif sw1 == 0x6F:
                    logger.error("Command aborted")
                else:
                    logger.error(f"Unexpected response: SW1={sw1:02X}, SW2={sw2:02X}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending APDU: {str(e)}")
            return {
                'data': None,
                'sw1': 0,
                'sw2': 0,
                'success': False
            }

class CardDataDisplay(QWidget):
    """Widget to display card data in a structured format."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Create text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setMinimumSize(400, 300)
        layout.addWidget(self.text_display)
        
        # Create print button
        self.print_button = QPushButton("Print Data")
        self.print_button.clicked.connect(self.print_data)
        self.print_button.setEnabled(False)
        layout.addWidget(self.print_button)
        
        self.setLayout(layout)
        
    def update_display(self, card_data):
        """Update the display with formatted card data."""
        try:
            logger.debug(f"Updating display with card data: {card_data}")
            # Ensure card_data is a dictionary
            if not isinstance(card_data, dict):
                if isinstance(card_data, str):
                    self.text_display.setPlainText(card_data)
                else:
                    self.text_display.setPlainText("Invalid card data format")
                self.print_button.setEnabled(False)
                return

            # Handle None or empty data
            if not card_data:
                self.text_display.setPlainText("No card data available")
                self.print_button.setEnabled(False)
                return

            # For dictionary data, format it nicely
            formatted = []
            
            # Basic info
            if 'card_type' in card_data:
                formatted.append(f"Card Type: {card_data['card_type']}")
            if 'status' in card_data:
                formatted.append(f"Status: {card_data['status']}")
            if 'message' in card_data:
                formatted.append(f"Message: {card_data['message']}")
            
            # ATR if available
            if 'atr' in card_data and isinstance(card_data['atr'], list):
                atr_str = ' '.join([f'{b:02X}' for b in card_data['atr']])
                formatted.append(f"\nATR: {atr_str}")
            else:
                logger.error("ATR data is not in expected format")
            
            # EMV data if available
            if 'emv_data' in card_data and isinstance(card_data['emv_data'], list):
                formatted.append("\nEMV Data:")
                for item in card_data['emv_data']:
                    if isinstance(item, dict) and 'type' in item and 'data' in item:
                        formatted.append(f"\n{item['type']}:\n")
                        if isinstance(item['data'], dict):
                            for tag, tag_data in item['data'].items():
                                if isinstance(tag_data, dict):
                                    desc = tag_data.get('description', 'Unknown Tag')
                                    decoded = tag_data.get('decoded', 'N/A')
                                    raw = tag_data.get('raw', '')
                                    formatted.append(f"  {desc} ({tag}):\n")
                                    formatted.append(f"    Raw: {raw}\n")
                                    formatted.append(f"    Decoded: {decoded}\n")
                                else:
                                    logger.error(f"Tag data for {tag} is not in expected format")
                        else:
                            logger.error(f"Data for {item['type']} is not in expected format")
                    else:
                        logger.error(f"EMV item is not in expected format: {item}")

            self.text_display.setPlainText('\n'.join(formatted))
            self.print_button.setEnabled(True)

        except Exception as e:
            error_msg = f"Error displaying card data: {str(e)}"
            logger.error(error_msg)
            self.text_display.setPlainText(error_msg)
            self.print_button.setEnabled(False)
    
    def print_data(self):
        """Print the card data."""
        dialog = QPrintDialog()
        if dialog.exec():
            printer = dialog.printer()
            self.text_display.print(printer)

class ImageDisplayWindow(QDialog):
    """Window to display captured images."""
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Captured Image")
        self.setModal(True)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Convert QImage to QPixmap for display
        pixmap = QPixmap.fromImage(image)
        
        # Scale the image to a reasonable size while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio, 
                                    Qt.TransformationMode.SmoothTransformation)
        
        # Create label and set the pixmap
        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to layout
        layout.addWidget(image_label)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Create video widget with a fixed size
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(400, 300)
        self.video_widget.setMaximumSize(400, 300)
        self.video_widget.setStyleSheet("QVideoWidget { background-color: black; }")
        layout.addWidget(self.video_widget)
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Create toggle camera button
        self.toggle_button = QPushButton("Start Camera")
        self.toggle_button.clicked.connect(self.toggle_camera)
        button_layout.addWidget(self.toggle_button)
        
        # Create switch camera button
        self.switch_camera_button = QPushButton("Switch Camera")
        self.switch_camera_button.clicked.connect(self.switch_camera)
        button_layout.addWidget(self.switch_camera_button)
        
        # Create capture button
        self.capture_button = QPushButton("Take Picture")
        self.capture_button.clicked.connect(self.capture_photo)
        self.capture_button.setEnabled(False)
        button_layout.addWidget(self.capture_button)
        
        # Add button layout to main layout
        layout.addLayout(button_layout)
        
        # Initialize camera-related variables
        self.camera = None
        self.capture_session = None
        self.image_capture = None
        self.video_sink = None
        self.current_camera_id = 0
        
        # Set the layout
        self.setLayout(layout)
        
        # Initialize camera
        QTimer.singleShot(100, self.initialize_camera)

    def switch_camera(self):
        """Switch between available cameras"""
        try:
            available_cameras = QMediaDevices().videoInputs()
            if len(available_cameras) < 2:
                QMessageBox.warning(self, "Warning", "No other cameras available")
                return
            
            # Stop current camera
            self.stop_camera()
            
            # Switch to next camera
            self.current_camera_id = (self.current_camera_id + 1) % len(available_cameras)
            
            # Initialize new camera
            self.initialize_camera()
            
            logger.debug(f"Switched to camera {self.current_camera_id}")
        except Exception as e:
            logger.error(f"Error switching camera: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", "Failed to switch camera")

    def capture_photo(self):
        """Capture a photo from the current camera"""
        try:
            if not self.image_capture:
                logger.error("Image capture not initialized")
                QMessageBox.warning(self, "Error", "Camera not properly initialized")
                return
            
            if not self.camera or not self.camera.isActive():
                logger.error("Camera not active")
                QMessageBox.warning(self, "Error", "Camera not active")
                return
            
            logger.debug("Attempting to capture photo...")
            self.image_capture.capture()
            
        except Exception as e:
            logger.error(f"Error capturing photo: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to capture photo: {str(e)}")

    def initialize_camera(self):
        """Initialize the camera with proper error handling."""
        try:
            # Get available cameras
            available_cameras = QMediaDevices().videoInputs()
            logger.info(f"Found {len(available_cameras)} camera(s)")
            if not available_cameras:
                logger.error("No cameras available")
                self.handle_camera_error(-1, "No cameras available")
                return

            # Stop any existing camera first
            self.stop_camera()
            
            # Get the camera device
            if self.current_camera_id >= len(available_cameras):
                self.current_camera_id = 0
            camera_device = available_cameras[self.current_camera_id]
            logger.info(f"Initializing camera: {camera_device.description()}")
            
            # Create new camera instance
            self.camera = QCamera(camera_device)
            if not self.camera:
                raise RuntimeError("Failed to create camera instance")
            self.camera.errorOccurred.connect(self.handle_camera_error)
            
            # Create and configure capture session
            self.capture_session = QMediaCaptureSession()
            if not self.capture_session:
                raise RuntimeError("Failed to create capture session")
            
            # Configure camera format before setting it in the capture session
            formats = camera_device.videoFormats()
            if formats:
                # Sort formats by resolution (width * height)
                sorted_formats = sorted(formats, 
                                     key=lambda f: f.resolution().width() * f.resolution().height())
                
                # Try to find an optimal format (prefer 640x480 or 1280x720)
                selected_format = None
                for fmt in sorted_formats:
                    resolution = fmt.resolution()
                    width = resolution.width()
                    height = resolution.height()
                    if ((width == 640 and height == 480) or 
                        (width == 1280 and height == 720)):
                        selected_format = fmt
                        logger.info(f"Selected optimal format: {width}x{height}")
                        break
                
                # If no optimal format found, use the middle resolution
                if not selected_format and formats:
                    selected_format = sorted_formats[len(sorted_formats)//2]
                    resolution = selected_format.resolution()
                    logger.info(f"Selected middle format: {resolution.width()}x{resolution.height()}")
                
                if selected_format:
                    self.camera.setCameraFormat(selected_format)
            
            # Set up video widget
            self.video_widget.setUpdatesEnabled(True)
            self.video_widget.show()
            self.video_widget.raise_()
            
            # Configure capture session
            self.capture_session.setCamera(self.camera)
            self.capture_session.setVideoOutput(self.video_widget)
            
            # Set up image capture
            self.image_capture = QImageCapture(self.camera)
            if not self.image_capture:
                raise RuntimeError("Failed to create image capture")
            self.image_capture.imageCaptured.connect(self.handle_image_captured)
            self.image_capture.errorOccurred.connect(self.handle_capture_error)
            self.capture_session.setImageCapture(self.image_capture)
            
            # Log successful initialization
            logger.info("Camera initialization completed successfully")
            self.toggle_button.setText("Stop Camera")
            
            # Start camera automatically
            QTimer.singleShot(100, self.start_camera)
            
        except Exception as e:
            logger.error(f"Error initializing camera: {str(e)}", exc_info=True)
            self.handle_camera_error(-1, f"Failed to initialize camera: {str(e)}")
            
    def start_camera(self):
        """Start the camera"""
        try:
            if not self.camera:
                logger.error("Cannot start: No camera initialized")
                return
                
            if self.camera.isActive():
                logger.debug("Camera is already active")
                return
                
            logger.debug(f"Starting camera {self.current_camera_id}")
            self.camera.start()
            
            # Update UI
            self.toggle_button.setText("Stop Camera")
            self.capture_button.setEnabled(True)
            
            # Verify camera started properly
            QTimer.singleShot(1000, self.check_camera_started)
            
        except Exception as e:
            logger.error(f"Error starting camera: {str(e)}", exc_info=True)
            self.handle_camera_error(-1, f"Failed to start camera: {str(e)}")

    def stop_camera(self):
        """Stop the camera"""
        try:
            if not self.camera:
                return
                
            logger.debug(f"Stopping camera {self.current_camera_id}")
            
            # First stop the camera if it's active
            if self.camera.isActive():
                self.camera.stop()
            
            # Clean up resources in the correct order
            if self.image_capture:
                try:
                    self.image_capture.imageCaptured.disconnect()
                    self.image_capture.errorOccurred.disconnect()
                except:
                    pass
                self.image_capture = None
            
            if self.capture_session:
                self.capture_session.setImageCapture(None)
                self.capture_session.setVideoOutput(None)
                self.capture_session.setCamera(None)
                self.capture_session = None
            
            if self.camera:
                try:
                    self.camera.errorOccurred.disconnect()
                except:
                    pass
                self.camera = None
            
            # Update UI
            self.toggle_button.setText("Start Camera")
            self.capture_button.setEnabled(False)
            
            # Clear video widget
            if self.video_widget:
                self.video_widget.update()
                
        except Exception as e:
            logger.error(f"Error stopping camera: {str(e)}", exc_info=True)

    def check_camera_started(self):
        """Check if the camera has started properly"""
        try:
            if not self.camera:
                logger.error("No camera instance available")
                return
                
            is_active = self.camera.isActive()
            logger.debug(f"Camera active: {is_active}")
            logger.debug(f"Video widget visible: {self.video_widget.isVisible()}")
            logger.debug(f"Video widget size: {self.video_widget.size()}")
            
            if is_active:
                # Verify capture session is properly configured
                if (self.capture_session and 
                    self.capture_session.camera() == self.camera and 
                    self.image_capture):
                    logger.info("Camera system initialized and running")
                    return
                    
            # If we get here, something is wrong
            logger.error("Camera system not properly initialized")
            self.stop_camera()
            self.handle_camera_error(-1, "Camera failed to initialize properly")
            
        except Exception as e:
            logger.error(f"Error checking camera: {str(e)}", exc_info=True)
            self.handle_camera_error(-1, f"Error checking camera: {str(e)}")

    def handle_image_captured(self, id, image):
        """Handle captured image"""
        try:
            logger.debug(f"Image captured with id: {id}")
            
            # Create and show the image display window
            display_window = ImageDisplayWindow(image, self)
            display_window.show()
                
        except Exception as e:
            logger.error(f"Error handling captured image: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error displaying photo: {str(e)}")

    def handle_capture_error(self, id, error, error_string):
        """Handle image capture errors"""
        logger.error(f"Capture error {id}: {error_string}")
        QMessageBox.critical(self, "Capture Error", f"Failed to capture image: {error_string}")

    def toggle_camera(self):
        """Toggle camera on/off"""
        try:
            if self.camera and self.camera.isActive():
                self.stop_camera()
            else:
                self.initialize_camera()
                
        except Exception as e:
            logger.error(f"Error toggling camera: {str(e)}", exc_info=True)
            self.handle_camera_error(-1, f"Failed to toggle camera: {str(e)}")

    def handle_camera_error(self, error, error_string):
        """Handle camera errors"""
        logger.error(f"Camera {self.current_camera_id} error: {error} - {error_string}")
        self.toggle_button.setText("Camera Error")
        self.capture_button.setEnabled(False)
        
        # Show error to user
        QMessageBox.critical(self, "Camera Error", 
                           f"Camera error occurred: {error_string}\n"
                           "Please try restarting the camera or switching to a different camera.")

class CardReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_card_polling()
        self.load_card_images()

    def load_card_images(self):
        """Load card brand images."""
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            images_dir = os.path.join(script_dir, 'images')
            
            # Load Visa image
            visa_path = os.path.join(images_dir, 'visa.png')
            logger.debug(f"Loading Visa image from: {visa_path}")
            self.visa_pixmap = QPixmap(visa_path)
            if self.visa_pixmap.isNull():
                logger.error(f"Failed to load Visa image from {visa_path}")
            else:
                self.visa_pixmap = self.visa_pixmap.scaled(400, 250, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                logger.debug(f"Loaded Visa image successfully")
            
            # Load Mastercard image
            mastercard_path = os.path.join(images_dir, 'mastercard.png')
            logger.debug(f"Loading Mastercard image from: {mastercard_path}")
            self.mastercard_pixmap = QPixmap(mastercard_path)
            if self.mastercard_pixmap.isNull():
                logger.error(f"Failed to load Mastercard image from {mastercard_path}")
            else:
                self.mastercard_pixmap = self.mastercard_pixmap.scaled(400, 250,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                logger.debug(f"Loaded Mastercard image successfully")
            
        except Exception as e:
            logger.error(f"Error loading card images: {str(e)}", exc_info=True)

    def init_ui(self):
        """Initialize the user interface."""
        try:
            # Set window properties
            self.setWindowTitle('Card Reader')
            self.setMinimumSize(1200, 800)
            
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            main_layout.setSpacing(10)
            
            # First row: Camera feed and card image side by side
            top_row = QHBoxLayout()
            top_row.setSpacing(10)

            # Camera widget (left)
            self.camera = CameraWidget()
            self.camera.parent = self
            top_row.addWidget(self.camera)

            # Card image (right)
            self.card_image = QLabel()
            self.card_image.setMinimumSize(400, 300)
            self.card_image.setMaximumSize(400, 300)
            self.card_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.card_image.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 2px solid #cccccc;
                    border-radius: 5px;
                }
            """)
            top_row.addWidget(self.card_image)

            # Ensure equal spacing on both sides
            top_row.setStretchFactor(self.camera, 1)
            top_row.setStretchFactor(self.card_image, 1)

            # Second row: Status logging
            self.status_text = QTextEdit()
            self.status_text.setReadOnly(True)
            self.status_text.setFixedHeight(100)
            self.status_text.setStyleSheet("QTextEdit { background-color: #f5f5f5; }")

            # Third row: Card info
            self.card_info = QTextEdit()
            self.card_info.setReadOnly(True)
            self.card_info.setMinimumHeight(150)
            self.card_info.setStyleSheet("QTextEdit { background-color: #f5f5f5; }")

            # Add all rows to main layout
            main_layout.addLayout(top_row)
            main_layout.addWidget(self.status_text)
            main_layout.addWidget(self.card_info)
            
        except Exception as e:
            logger.error(f"Error initializing UI: {str(e)}", exc_info=True)

    def start_card_polling(self):
        """Start the card polling thread."""
        self.poll_thread = threading.Thread(target=self.poll_cards, daemon=True)
        self.poll_thread.start()

    def poll_cards(self):
        """Poll for card presence and read card data."""
        try:
            while True:
                try:
                    # Get available readers
                    available_readers = readers()
                    
                    # Try to connect to card
                    connection = None
                    for reader in available_readers:
                        try:
                            connection = reader.createConnection()
                            connection.connect()
                            break
                        except Exception:
                            continue
                    
                    if connection:
                        current_atr = toHexString(connection.getATR())
                        logger.debug(f"New card detected with ATR: {current_atr}")
                        
                        # Use QMetaObject.invokeMethod to safely update UI from another thread
                        QMetaObject.invokeMethod(self.status_text, "setText", 
                            Qt.ConnectionType.QueuedConnection,
                            Q_ARG(str, 'Reading card data... Please hold the card'))
                        
                        # Detect card type
                        card_reader = CardReader()
                        card_type = card_reader.detect_card_type(connection)
                        
                        # Update card image based on card type
                        if card_type:
                            if card_type.lower() == 'visa' and hasattr(self, 'visa_pixmap'):
                                QMetaObject.invokeMethod(self.card_image, "setPixmap",
                                    Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(QPixmap, self.visa_pixmap))
                                    
                            elif card_type.lower() == 'mastercard' and hasattr(self, 'mastercard_pixmap'):
                                QMetaObject.invokeMethod(self.card_image, "setPixmap",
                                    Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(QPixmap, self.mastercard_pixmap))
                            
                            # Get current camera info if it exists
                            current_text = self.card_info.toPlainText()
                            camera_info = ""
                            if "Camera Information:" in current_text:
                                camera_info = current_text.split("Card Information:")[0] if "Card Information:" in current_text else current_text
                                camera_info += "\n"
                            
                            # Read and decode card data
                            try:
                                card_data = card_reader.read_card_data(connection, card_type)
                                logger.debug(f"Type of card_data: {type(card_data)}")
                                if not isinstance(card_data, dict):
                                    logger.error("Card data is not a dictionary")
                                    self.card_data_display.update_display(f"Invalid card data format: {str(card_data)}")
                                    return

                                if card_data.get('status') != 'success':
                                    self.card_data_display.update_display(f"Error reading card: {card_data.get('status', 'Unknown error')}")
                                    return
                                
                                # Format the data as a simple string
                                card_info = camera_info + "Card Information:\n"
                                card_info += f"Card Type: {card_type}\n"
                                card_info += f"ATR: {current_atr}\n\n"
                                
                                if card_data.get('emv_data'):
                                    card_info += "EMV Data:\n"
                                    for item in card_data['emv_data']:
                                        if isinstance(item, dict) and 'type' in item and 'data' in item:
                                            card_info += f"\n{item['type']}:\n"
                                            if isinstance(item['data'], dict):
                                                for tag, tag_data in item['data'].items():
                                                    if isinstance(tag_data, dict):
                                                        desc = tag_data.get('description', 'Unknown Tag')
                                                        decoded = tag_data.get('decoded', 'N/A')
                                                        raw = tag_data.get('raw', '')
                                                        card_info += f"  {desc} ({tag}):\n"
                                                        card_info += f"    Raw: {raw}\n"
                                                        card_info += f"    Decoded: {decoded}\n"
                                                    else:
                                                        logger.error(f"Tag data for {tag} is not in expected format")
                                            else:
                                                logger.error(f"Data for {item['type']} is not in expected format")
                                        else:
                                            logger.error(f"EMV item is not in expected format: {item}")
                                # Update card info text
                                QMetaObject.invokeMethod(self.card_info, "setText",
                                    Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(str, card_info))
                                
                                QMetaObject.invokeMethod(self.status_text, "setText",
                                    Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(str, f'Successfully read {card_type} card'))
                                
                            except Exception as e:
                                logger.error(f"Error processing card data: {str(e)}")
                                error_info = camera_info + f"Card Information:\nCard Type: {card_type}\nError reading card data: {str(e)}"
                                QMetaObject.invokeMethod(self.card_info, "setText",
                                    Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(str, error_info))
                        else:
                            QMetaObject.invokeMethod(self.status_text, "setText",
                                Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, 'Unknown card type'))
                    
                    time.sleep(1)  # Poll every second
                    
                except Exception as e:
                    if "Card is not present" not in str(e):
                        logger.error(f"Error in card polling: {str(e)}")
                    time.sleep(1)  # Wait before retrying
                    
        except Exception as e:
            logger.error(f"Fatal error in polling thread: {str(e)}", exc_info=True)

def main():
    try:
        logger.debug("Starting application")

        # Enable debug output for QCamera
        os.environ['QT_DEBUG_PLUGINS'] = '1'

        app = QApplication(sys.argv)

        # List available cameras
        available_cameras = QMediaDevices().videoInputs()
        logger.debug("Available cameras:")
        for i, camera in enumerate(available_cameras):
            logger.debug(f"Camera {i}: {camera.description()}")

        window = CardReaderApp()
        window.show()
        logger.debug("Application window shown")
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
