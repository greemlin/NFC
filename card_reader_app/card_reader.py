import sys
import os
import threading
import time
import queue
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QFrame, QTextEdit, QPlainTextEdit)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QPixmap, QFont
from smartcard.System import readers
from smartcard.util import toHexString, toBytes
from smartcard.Exceptions import NoCardException, CardConnectionException
from datetime import datetime

# EMV Tag Definitions
EMV_TAGS = {
    # Basic Data Elements
    '5A': 'Application Primary Account Number (PAN)',
    '5F20': 'Cardholder Name',
    '5F24': 'Application Expiration Date',
    '5F25': 'Application Effective Date',
    '5F28': 'Issuer Country Code',
    '5F2A': 'Transaction Currency Code',
    '5F30': 'Service Code',
    '5F34': 'Application PAN Sequence Number',
    '5F2D': 'Language Preference',
    '50': 'Application Label',
    '4F': 'Application Identifier (AID)',
    '57': 'Track 2 Equivalent Data',

    # Application Data
    '82': 'Application Interchange Profile',
    '84': 'Dedicated File Name',
    '87': 'Application Priority Indicator',
    '88': 'Short File Identifier (SFI)',
    '8C': 'Card Risk Management Data Object List 1 (CDOL1)',
    '8D': 'Card Risk Management Data Object List 2 (CDOL2)',
    '8E': 'Cardholder Verification Method (CVM) List',
    '8F': 'Certification Authority Public Key Index',

    # Security Related
    '90': 'Issuer Public Key Certificate',
    '92': 'Issuer Public Key Remainder',
    '93': 'Signed Static Application Data',
    '94': 'Application File Locator (AFL)',
    '95': 'Terminal Verification Results',
    '9F32': 'Issuer Public Key Exponent',
    '9F46': 'ICC Public Key Certificate',
    '9F47': 'ICC Public Key Exponent',
    '9F48': 'ICC Public Key Remainder',
    '9F4A': 'Static Data Authentication Tag List',
    '9F4C': 'ICC Dynamic Number',

    # Transaction Related
    '9A': 'Transaction Date',
    '9B': 'Transaction Status Information',
    '9C': 'Transaction Type',
    '9F02': 'Amount, Authorized',
    '9F03': 'Amount, Other',
    '9F1A': 'Terminal Country Code',
    '9F1F': 'Track 1 Discretionary Data',
    '9F20': 'Track 2 Discretionary Data',
    '9F26': 'Application Cryptogram',
    '9F27': 'Cryptogram Information Data',
    '9F36': 'Application Transaction Counter (ATC)',
    '9F37': 'Unpredictable Number',
    '9F42': 'Application Currency Code',
    '9F44': 'Application Currency Exponent',

    # Application Control
    '9F07': 'Application Usage Control',
    '9F08': 'Application Version Number',
    '9F09': 'Application Version Number (Terminal)',
    '9F0D': 'Issuer Action Code - Default',
    '9F0E': 'Issuer Action Code - Denial',
    '9F0F': 'Issuer Action Code - Online',
    
    # Card Holder Verification
    '9F34': 'Cardholder Verification Method (CVM) Results',
    '9F35': 'Terminal Type',
    '9F6C': 'Card Transaction Qualifiers (CTQ)',
    
    # Additional Data
    '9F5B': 'Issuer Script Results',
    '9F6E': 'Form Factor Indicator',
    '9F7C': 'Customer Exclusive Data'
}

class CardReader:
    def __init__(self):
        """Initialize card reader with EMV tag definitions."""
        self.emv_tags = {
            # Basic EMV Tags
            '42': 'Issuer Identification Number (IIN)',
            '4F': 'Application Dedicated File (ADF) Name',
            '50': 'Application Label',
            '57': 'Track 2 Equivalent Data',
            '5A': 'Application Primary Account Number (PAN)',
            '5F20': 'Cardholder Name',
            '5F24': 'Application Expiration Date',
            '5F25': 'Application Effective Date',
            '5F28': 'Issuer Country Code',
            '5F2A': 'Transaction Currency Code',
            '5F2D': 'Language Preference',
            '5F30': 'Service Code',
            '5F34': 'Application Primary Account Number (PAN) Sequence Number',
            '5F36': 'Transaction Currency Exponent',
            
            # Template Related Tags
            '61': 'Application Template',
            '6F': 'File Control Information (FCI) Template',
            '70': 'EMV Proprietary Template',
            '71': 'Issuer Script Template 1',
            '72': 'Issuer Script Template 2',
            '73': 'Directory Discretionary Template',
            '77': 'Response Message Template Format 2',
            '80': 'Response Message Template Format 1',
            
            # Processing Tags
            '82': 'Application Interchange Profile',
            '83': 'Command Template',
            '84': 'Dedicated File (DF) Name',
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
            
            # BF Series Tags
            'BF0C': 'File Control Information (FCI) Issuer Discretionary Data',
            
            # Additional NFC Tags
            '9F6E': 'Form Factor Indicator',
            '9F7C': 'Customer Exclusive Data',
            
            # Advanced Tags
            'A5': 'File Control Information (FCI) Proprietary Template',
            'DF01': 'Proprietary Data Element',
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
            '9F5B': 'Issuer URL3',
            '9F5C': 'Upper Cumulative Total Transaction Amount Limit',
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
            '9F7D': 'Application Specific Transparent Template',
            
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
        self.connection = None
        self.reader = None
        self.card_type = None
        self.last_atr = None

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
            print(f"Error decoding ATR: {e}")
            return atr

    def try_decode_unknown(self, value):
        """Try to decode unknown values as string or number."""
        try:
            # Remove any spaces from the hex string
            value = value.replace(' ', '')
            
            # Try to decode as ASCII string if length is reasonable
            if len(value) >= 2:  # At least 1 byte
                try:
                    ascii_str = bytes.fromhex(value).decode('ascii', errors='ignore')
                    ascii_str = ''.join(c if c.isprintable() else '' for c in ascii_str)
                    if len(ascii_str) > 2:  # If contains enough printable chars
                        return f"ASCII: {ascii_str}"
                except:
                    pass

            # Try as number (both decimal and BCD)
            if len(value) <= 8:  # Reasonable length for a number
                try:
                    # Try as decimal
                    decimal = int(value, 16)
                    if decimal < 1000000:  # Reasonable number size
                        return f"Number: {decimal}"
                except:
                    pass
                
                # Try as BCD (Binary Coded Decimal)
                if all(c in '0123456789' for c in value):
                    return f"BCD: {value}"
            
            # Format hex in simple groups of 2
            hex_bytes = [value[i:i+2] for i in range(0, len(value), 2)]
            return f"HEX: {' '.join(hex_bytes)}"
                
        except Exception as e:
            print(f"Error in try_decode_unknown: {e}")
            return value

    def decode_emv_value(self, tag, value):
        """Decode EMV value based on tag type with enhanced parsing."""
        try:
            tag_name = self.emv_tags.get(tag, 'Unknown Tag')
            
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
            return f"{tag_name}: {value}"
            
        except Exception as e:
            print(f"Error decoding tag {tag}: {str(e)}")
            return f"Error decoding {tag}: {value}"

    def parse_tlv(self, hex_string, level=0):
        """Parse TLV (Tag Length Value) data from hex string."""
        tlv_data = []
        i = 0
        
        while i < len(hex_string):
            try:
                # Get Tag
                tag = hex_string[i:i+2]
                i += 2
                
                # Check for extended tag
                while int(tag[-2:], 16) & 0x1F == 0x1F:
                    if i >= len(hex_string):
                        break
                    tag += hex_string[i:i+2]
                    i += 2
                
                if i >= len(hex_string):
                    break
                
                # Get Length
                length = int(hex_string[i:i+2], 16)
                i += 2
                
                # Check for extended length
                if length & 0x80:
                    num_bytes = length & 0x7F
                    if num_bytes > 0:
                        length = int(hex_string[i:i+num_bytes*2], 16)
                        i += num_bytes * 2
                
                # Get Value
                value = hex_string[i:i+length*2]
                i += length * 2
                
                # Handle template tags (nested TLV)
                if tag in ['70', '77', '80', '84', 'A5', '6F', '61']:
                    nested_data = self.parse_tlv(value, level + 1)
                    tlv_data.extend(nested_data)
                else:
                    # Try to decode the value based on tag
                    decoded = self.decode_emv_value(tag, value)
                    
                    tlv_data.append({
                        'tag': tag,
                        'length': length,
                        'value': value,
                        'decoded': decoded,
                        'level': level
                    })
                
            except Exception as e:
                print(f"Error parsing TLV at position {i}: {str(e)}")
                break
        
        return tlv_data

    def read_card_data(self, connection, card_type):
        """Read EMV card data after selecting the appropriate AID."""
        data = []
        try:
            # Get list of applications (PSE)
            pse_apdu = [0x00, 0xA4, 0x04, 0x00, 0x0E, 0x31, 0x50, 0x41, 0x59, 0x2E, 0x53, 0x59, 0x53, 0x2E, 0x44, 0x44, 0x46, 0x30, 0x31]
            response, sw1, sw2 = self.send_apdu(connection, pse_apdu)
            
            # Try to get applications list
            if sw1 == 0x90:
                # Read PSE record
                read_pse = [0x00, 0xB2, 0x01, 0x0C, 0x00]
                response, sw1, sw2 = self.send_apdu(connection, read_pse)
                if sw1 == 0x90:
                    pse_data = self.parse_tlv(toHexString(response).replace(' ', ''))
                    data.append({
                        'sfi': 'PSE',
                        'record': 1,
                        'data': pse_data
                    })

            # Select the appropriate AID based on card type
            if card_type == "VISA":
                aids = [
                    [0xA0, 0x00, 0x00, 0x00, 0x03, 0x10, 0x10],  # Visa Credit/Debit
                    [0xA0, 0x00, 0x00, 0x00, 0x03, 0x20, 0x10],  # Visa Electron
                    [0xA0, 0x00, 0x00, 0x00, 0x03, 0x30, 0x10]   # Visa V PAY
                ]
            elif card_type == "MASTERCARD":
                aids = [
                    [0xA0, 0x00, 0x00, 0x00, 0x04, 0x10, 0x10],  # Mastercard Credit/Debit
                    [0xA0, 0x00, 0x00, 0x00, 0x04, 0x30, 0x60],  # Maestro
                    [0xA0, 0x00, 0x00, 0x00, 0x04, 0x60, 0x00]   # Cirrus
                ]
            else:
                return data

            # Try each AID
            for aid in aids:
                select_aid = [0x00, 0xA4, 0x04, 0x00, len(aid)] + aid + [0x00]
                response, sw1, sw2 = self.send_apdu(connection, select_aid)
                
                if sw1 == 0x90:
                    # Get Processing Options (PDOL)
                    gpo = [0x80, 0xA8, 0x00, 0x00, 0x02, 0x83, 0x00]
                    response, sw1, sw2 = self.send_apdu(connection, gpo)
                    
                    # Read all possible records
                    for sfi in range(1, 32):  # SFI range
                        for record in range(1, 17):  # Record range
                            cmd = [0x00, 0xB2, record, (sfi << 3) | 0x04, 0x00]
                            response, sw1, sw2 = self.send_apdu(connection, cmd)
                            
                            if sw1 == 0x90:
                                hex_data = toHexString(response).replace(' ', '')
                                tlv_data = self.parse_tlv(hex_data)
                                if tlv_data:  # Only add if we got valid TLV data
                                    data.append({
                                        'sfi': sfi,
                                        'record': record,
                                        'data': tlv_data
                                    })
                            elif sw1 != 0x6A and sw2 != 0x83:  # Skip "record not found" error
                                print(f"Record read failed - SFI: {sfi}, Record: {record}, SW1: {hex(sw1)}, SW2: {hex(sw2)}")

                    # Try to read transaction log
                    log_entry = [0x00, 0xB2, 0x01, 0x5C, 0x00]  # Typical location for log entries
                    response, sw1, sw2 = self.send_apdu(connection, log_entry)
                    if sw1 == 0x90:
                        hex_data = toHexString(response).replace(' ', '')
                        tlv_data = self.parse_tlv(hex_data)
                        if tlv_data:
                            data.append({
                                'sfi': 'LOG',
                                'record': 1,
                                'data': tlv_data
                            })

                    # Get PIN try counter
                    pin_try_counter = [0x80, 0xCA, 0x9F, 0x17, 0x00]
                    response, sw1, sw2 = self.send_apdu(connection, pin_try_counter)
                    if sw1 == 0x90:
                        hex_data = toHexString(response).replace(' ', '')
                        tlv_data = self.parse_tlv(hex_data)
                        if tlv_data:
                            data.append({
                                'sfi': 'PIN',
                                'record': 'try_counter',
                                'data': tlv_data
                            })

        except Exception as e:
            print(f"Error reading EMV data: {str(e)}")

        return data

    def summarize_card_data(self, data):
        """Extract and summarize key card information."""
        summary = {
            'card_number': None,
            'expiry_date': None,
            'aid': None,
            'app_name': None,
            'app_count': 0,
            'issuer': None,
            'services': [],
            'card_type': None,
            'transaction_count': None,
            'pin_tries': None,
            'transactions': [],
            'logs': []
        }
        
        for record in data:
            for tlv in record['data']:
                tag = tlv['tag']
                value = tlv['value']
                
                if tag == '5A':  # PAN
                    summary['card_number'] = ' '.join(value[i:i+4] for i in range(0, len(value), 4))
                elif tag == '5F24':  # Expiry Date
                    try:
                        summary['expiry_date'] = datetime.strptime(value, '%y%m%d').strftime('%Y-%m-%d')
                    except:
                        summary['expiry_date'] = value
                elif tag == '4F':  # AID
                    summary['aid'] = value
                elif tag == '50':  # Application Label
                    try:
                        summary['app_name'] = bytes.fromhex(value).decode('ascii').strip()
                    except:
                        summary['app_name'] = value
                elif tag == '5F20':  # Issuer name
                    try:
                        summary['issuer'] = bytes.fromhex(value).decode('ascii').strip()
                    except:
                        summary['issuer'] = value
                elif tag == '9F36':  # Transaction Counter
                    try:
                        summary['transaction_count'] = int(value, 16)
                    except:
                        summary['transaction_count'] = value
                elif tag == '9F17':  # PIN Try Counter
                    try:
                        summary['pin_tries'] = int(value, 16)
                    except:
                        summary['pin_tries'] = value
                elif tag == '9F07':  # Application Usage Control
                    try:
                        auc = int(value, 16)
                        if auc & 0x80: summary['services'].append("ATM")
                        if auc & 0x40: summary['services'].append("Non-ATM")
                        if auc & 0x20: summary['services'].append("Domestic")
                        if auc & 0x10: summary['services'].append("International")
                    except:
                        pass
                
                # Look for transaction logs
                if record['sfi'] == 'LOG':
                    summary['logs'].append(value)
        
        return summary

    def detect_card_type(self, connection):
        """Detect if card is Visa or Mastercard."""
        try:
            # Try Mastercard AID
            mastercard_aid = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x04, 0x10, 0x10, 0x00]
            response, sw1, sw2 = self.send_apdu(connection, mastercard_aid)
            if sw1 == 0x90:
                return "MASTERCARD"

            # Try Visa AID
            visa_aid = [0x00, 0xA4, 0x04, 0x00, 0x07, 0xA0, 0x00, 0x00, 0x00, 0x03, 0x10, 0x10, 0x00]
            response, sw1, sw2 = self.send_apdu(connection, visa_aid)
            if sw1 == 0x90:
                return "VISA"

        except Exception as e:
            print(f"Error detecting card type: {str(e)}")
        return None

    def send_apdu(self, connection, apdu):
        """Send APDU command to card and return response."""
        try:
            response, sw1, sw2 = connection.transmit(apdu)
            return response, sw1, sw2
        except Exception as e:
            print(f"Error sending APDU: {str(e)}")
            return None, None, None

class ModernFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            ModernFrame {
                background-color: #ffffff;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)

class CardReaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.message_queue = queue.Queue()
        self.running = True
        self.card_reader = CardReader()
        self.init_ui()
        self.load_card_images()
        self.start_monitoring()
        
        # Setup message processing timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_messages)
        self.timer.start(100)
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('Printec Payment Card Reader')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #2c3e50;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', monospace;
                font-size: 14px;
                color: #2c3e50;
            }
        """)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Top section (Header, Status, Image, Name)
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        self.header_label = QLabel('Printec Payment Card Reader')
        self.header_label.setFont(QFont('Segoe UI', 32, QFont.Weight.Bold))
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(self.header_label)
        
        # Status
        status_frame = ModernFrame()
        status_layout = QVBoxLayout(status_frame)
        self.status_label = QLabel('Waiting for Card...')
        self.status_label.setFont(QFont('Segoe UI', 16))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.status_label)
        top_layout.addWidget(status_frame)
        
        # Card Image (Centered)
        card_frame = ModernFrame()
        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.card_image_label = QLabel()
        self.card_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_image_label.setFixedSize(200, 200)
        self.card_image_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
        """)
        card_layout.addWidget(self.card_image_label)
        top_layout.addWidget(card_frame)
        
        # Cardholder Name
        cardholder_frame = ModernFrame()
        cardholder_layout = QVBoxLayout(cardholder_frame)
        self.cardholder_label = QLabel('')
        self.cardholder_label.setFont(QFont('Segoe UI', 24, QFont.Weight.Bold))
        self.cardholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cardholder_layout.addWidget(self.cardholder_label)
        top_layout.addWidget(cardholder_frame)
        
        layout.addWidget(top_widget)
        
        # Card Data Display
        data_frame = ModernFrame()
        data_layout = QVBoxLayout(data_frame)
        
        data_header = QLabel('Decoded Card Data')
        data_header.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        data_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        data_layout.addWidget(data_header)
        
        self.data_display = QPlainTextEdit()
        self.data_display.setReadOnly(True)
        self.data_display.setMinimumHeight(300)
        self.data_display.setFont(QFont('Consolas', 12))
        data_layout.addWidget(self.data_display)
        
        layout.addWidget(data_frame)
        
        # Set window size and position
        self.resize(800, 900)
        self.center_window()
        
    def center_window(self):
        """Center the window on the screen."""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
        
    @pyqtSlot()
    def process_messages(self):
        """Process messages from the card monitoring thread."""
        try:
            while True:
                try:
                    msg_type, msg_data = self.message_queue.get_nowait()
                    
                    if msg_type == 'status':
                        self.status_label.setText(msg_data)
                        
                    elif msg_type == 'card':
                        card_type, atr, card_data = msg_data
                        self.last_card_data = msg_data
                        
                        # Update status
                        self.status_label.setText('Card detected')
                        
                        # Update card image
                        if card_type and card_type.lower() in self.card_images:
                            pixmap = self.card_images[card_type.lower()]
                            self.card_image_label.setPixmap(pixmap)
                        else:
                            self.card_image_label.clear()
                        
                        # Update cardholder name
                        self.cardholder_label.setText(card_type)
                        
                        # Update card data display with decoded EMV data
                        display_text = f"Card Type: {card_type}\n"
                        display_text += f"ATR: {self.card_reader.decode_atr(atr)}\n\n"
                        
                        # Add EMV data
                        display_text += "=== EMV Card Data ===\n"
                        for record in card_data:
                            if record['sfi'] == 'PSE':
                                display_text += "\nPayment System Environment (PSE)\n"
                            elif record['sfi'] == 'LOG':
                                display_text += "\nTransaction Log\n"
                            elif record['sfi'] == 'PIN':
                                display_text += "\nPIN Information\n"
                            else:
                                display_text += f"\nSFI: {record['sfi']}, Record: {record['record']}\n"
                            
                            display_text += "-" * 50 + "\n"
                            
                            # Process TLV data
                            for tlv in record['data']:
                                # Skip template tags as their content is already included
                                if tlv['tag'] not in ['70', '77', '80', '84', 'A5', '6F', '61']:
                                    indent = "  " * tlv.get('level', 0)
                                    display_text += f"{indent}{tlv['decoded']}\n"
                        
                        self.data_display.setPlainText(display_text)
                            
                except queue.Empty:
                    break
                    
        except Exception as e:
            print(f"Error processing messages: {e}")
            
    def load_card_images(self):
        """Load and resize card brand images."""
        self.card_images = {}
        image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        print(f"Loading images from: {image_dir}")
        
        for brand in ['visa', 'mastercard']:
            try:
                image_path = os.path.join(image_dir, f'{brand}.png')
                print(f"Looking for {brand} image at: {image_path}")
                if os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        self.card_images[brand] = pixmap
                        print(f"Loaded {brand} image: {pixmap.width()}x{pixmap.height()}")
                    else:
                        print(f"Failed to load {brand} image")
                else:
                    print(f"Image not found: {image_path}")
            except Exception as e:
                print(f"Error loading {brand} image: {e}")
                
    def start_monitoring(self):
        """Start the card monitoring thread."""
        self.monitor_thread = threading.Thread(target=self.monitor_cards, daemon=True)
        self.monitor_thread.start()
        
    def monitor_cards(self):
        """Monitor for card presence and read card data."""
        last_atr = None
        
        while self.running:
            try:
                # Get all available readers
                available_readers = readers()
                if not available_readers:
                    time.sleep(1)
                    continue

                reader = available_readers[0]
                connection = reader.createConnection()
                
                try:
                    connection.connect()
                    current_atr = toHexString(connection.getATR())
                    
                    # Only process if it's a new card
                    if current_atr != last_atr:
                        last_atr = current_atr
                        print(f"New card detected with ATR: {current_atr}")
                        card_type = self.card_reader.detect_card_type(connection)
                        print(f"Detected card type: {card_type}")
                        
                        # Read EMV card data
                        card_data = self.card_reader.read_card_data(connection, card_type)
                        
                        # Send card type, ATR, and EMV data
                        self.message_queue.put(('card', (card_type, current_atr, card_data)))
                        
                except Exception as e:
                    print(f"Error connecting to card: {str(e)}")
                    last_atr = None
                    if "No smart card inserted" in str(e):
                        self.message_queue.put(('status', 'Waiting for Card...'))
                    else:
                        self.message_queue.put(('status', f'Error reading card: {str(e)}'))
                    
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in monitor_cards: {str(e)}")
                time.sleep(1)
                
    def closeEvent(self, event):
        """Handle application closing."""
        self.running = False
        event.accept()

def main():
    try:
        app = QApplication(sys.argv)
        
        # Set application style
        app.setStyle('Fusion')
        
        # Create and show the main window
        window = CardReaderApp()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
