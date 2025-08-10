#!/usr/bin/env python3
"""
Convert Excel file to UOB FAST/GIRO TXT format with Payment Advice
According to Format Specification v4.8
"""

import pandas as pd
import sys
from datetime import datetime
import argparse

# Bank code mapping
BANK_MAPPING = {
    'DBS/POSB - 7171': 'DBSSSGSGXXX',
    'OCBC - 7339': 'OCBCSGSGXXX',
    'UOB - 7375': 'UOVBSGSGXXX',
    'Standard Chartered - 9496': 'SCBLSGSGXXX',
    'HSBC - 7232': 'HSBCSGSGXXX',
    'Citibank - 7214': 'CITISGSGXXX',
    'Maybank - 7302': 'MBBESGSGXXX',
    'Maybank Singapore Limited - 7302': 'MBBESGSGXXX',
    'Bank of China - 7366': 'BKCHSGSGXXX'
}

def pad_right(text, length):
    """Pad text with spaces to the right to reach specified length"""
    if text is None:
        text = ''
    text = str(text)[:length]  # Truncate if too long
    return text.ljust(length, ' ')

def pad_left_zero(number, length):
    """Pad number with zeros to the left to reach specified length"""
    return str(int(number)).zfill(length)

def format_amount(amount):
    """Format amount as 18 digits with leading zeros, no decimals"""
    # Convert to cents (multiply by 100)
    cents = int(float(amount) * 100)
    return pad_left_zero(cents, 18)

def compute_field_check_summary(field_value, hash_index):
    """Compute field check summary according to spec"""
    total = 0
    for i in range(min(len(field_value), hash_index)):
        ascii_val = ord(field_value[i])
        total += (i + 1) * ascii_val
    return total

def calculate_hash_total(header_record, detail_records):
    """Calculate hash total according to Appendix 4 of the specification"""
    
    # Extract header fields for hash calculation
    # Positions are 0-based in Python (spec uses 1-based)
    orig_bic = header_record[35:46]  # Position 36-46 in spec
    orig_acc = header_record[49:83]  # Position 50-83 in spec 
    orig_name = header_record[83:223]  # Position 84-223 in spec
    payment_type = header_record[11]  # Position 12 in spec
    
    # Header calculations
    sum1 = compute_field_check_summary(orig_bic, 11)
    sum2 = compute_field_check_summary(orig_acc, 34)
    sum3 = compute_field_check_summary(orig_name, 140)
    total1 = sum1 + sum2 + sum3
    
    # Set payment code based on payment type
    if payment_type == 'P':
        payment_code = 20
    elif payment_type == 'R':
        payment_code = 22
    else:  # 'C'
        payment_code = 30
    
    # Process detail records
    total2 = 0
    hash_code = 0
    
    for record in detail_records:
        # Update hash code
        if hash_code == 9:
            hash_code = 1
        else:
            hash_code += 1
            
        # Extract fields (0-based positions)
        recv_bic = record[7:18]  # Position 8-18
        recv_acc = record[18:52]  # Position 19-52 
        recv_name = record[52:192]  # Position 53-192
        currency = record[186:189]  # Position 187-189
        amount = record[189:207]  # Position 190-207
        purpose = record[277:281]  # Position 278-281
        
        # Calculate sums
        sum1 = compute_field_check_summary(recv_bic, 11)
        sum2 = compute_field_check_summary(recv_acc, 34) * hash_code
        sum3 = compute_field_check_summary(recv_name, 140) * hash_code
        sum4 = compute_field_check_summary(currency, 3)
        sum5 = compute_field_check_summary(amount, 18)
        sum6 = compute_field_check_summary(purpose, 4)
        
        sum7 = sum1 + sum2 + sum3 + sum4 + sum5 + sum6 + (payment_code * hash_code)
        total2 += sum7
    
    # Final check sum
    final_check_sum = total1 + total2
    
    # Return as 16-digit string
    return str(final_check_sum)[-16:].zfill(16)

def create_header_record(file_name, creation_date_long, value_date):
    """Create Type 1 - Batch Header Record (1055 chars for Payment Advice)"""
    record = ''
    
    # Build header according to exact spec positions
    record += '1'                                          # 1: Record Type
    record += pad_right(file_name[:10], 10)                # 2-11: File Name (10 chars, not 14!)
    record += 'P'                                          # 12: Payment Type (P for Payment)
    record += pad_right('NORMAL', 10)                      # 13-22: Service Type (10 chars)
    record += 'I'                                          # 23: Processing Mode (I for FAST)
    record += pad_right('', 12)                            # 24-35: Company ID (12 chars) - conditional
    record += pad_right('UOVBSGSGXXX', 11)                # 36-46: Originating BIC (11 chars)
    record += 'SGD'                                        # 47-49: Currency (3 chars)
    record += pad_right('3663050778', 34)                  # 50-83: Originating Account Number (34 chars)
    record += pad_right('SINGAPORE OLYMPIC FOUNDATION', 140)  # 84-223: Originating Account Name (140 chars)
    record += creation_date_long                           # 224-231: File Creation Date YYYYMMDD (8 chars)
    record += value_date                                   # 232-239: Value Date YYYYMMDD (8 chars)
    record += pad_right('', 140)                           # 240-379: Ultimate Originating Customer (140 chars)
    record += pad_right('SOFPLSAWARD', 16)                 # 380-395: Bulk Customer Reference (16 chars)
    record += pad_right('', 10)                            # 396-405: Software Label (10 chars)
    record += pad_right('', 105)                           # 406-510: Payment Advice Header Line 1 (105 chars)
    record += pad_right('', 105)                           # 511-615: Payment Advice Header Line 2 (105 chars)
    record += pad_right('', 440)                           # 616-1055: Filler (440 chars)
    
    return record[:1055]  # Ensure exactly 1055 chars

def create_detail_record(row, seq_num):
    """Create Type 2 - Payment Instruction Detail Record (1055 chars for Payment Advice)"""
    # Get bank code
    bank_code = BANK_MAPPING.get(row['Bank'], 'DBSSSGSGXXX')
    
    # Format account number - remove decimals if present
    account_num = str(row['Bank Account Number ']).replace('.0', '').replace('.', '')
    
    # Build record with exact field positions from spec
    record = ''
    record += '2'                                          # 1: Record Type
    record += pad_right(bank_code, 11)                     # 2-12: Receiving Bank BIC (11 chars)
    record += pad_right(account_num, 34)                   # 13-46: Receiving Account Number (34 chars)
    record += pad_right(row['Bank Account Name'][:140], 140)  # 47-186: Receiving Account Name (140 chars)
    record += 'SGD'                                        # 187-189: Currency Code (3 chars)
    record += format_amount(row['Amount'])                 # 190-207: Amount (18 chars)
    record += pad_right(f'REF{seq_num:04d}', 35)           # 208-242: End to End ID (35 chars)
    record += pad_right('', 35)                            # 243-277: Mandate ID (35 chars)
    record += 'OTHR'                                       # 278-281: Purpose Code (4 chars)
    record += pad_right('SOFPLS SCHOLARSHIP', 140)         # 282-421: Remittance Information (140 chars)
    record += pad_right('', 140)                           # 422-561: Ultimate Payer/Beneficiary (140 chars)
    record += pad_right('', 16)                            # 562-577: Customer Reference (16 chars)
    
    # Payment Advice fields
    record += 'Y'                                          # 578: Payment Advice Indicator
    record += ' '                                          # 579: Delivery Mode (Post) - blank
    record += 'E'                                          # 580: Delivery Mode (Email)
    record += pad_right('', 2)                             # 581-582: Filler (2 chars)
    record += '2'                                          # 583: Advice Format
    record += pad_right(row['Name of Recipient '][:35], 35)   # 584-618: Beneficiary Name Line 1 (35 chars)
    record += pad_right('', 35)                            # 619-653: Beneficiary Name Line 2 (35 chars)
    record += pad_right('', 35)                            # 654-688: Beneficiary Name Line 3 (35 chars)
    record += pad_right('', 35)                            # 689-723: Beneficiary Name Line 4 (35 chars)
    record += pad_right('', 35)                            # 724-758: Beneficiary Address Line 1 (35 chars)
    record += pad_right('', 35)                            # 759-793: Beneficiary Address Line 2 (35 chars)
    record += pad_right('', 35)                            # 794-828: Beneficiary Address Line 3 (35 chars)
    record += pad_right('', 35)                            # 829-863: Beneficiary Address Line 4 (35 chars)
    record += pad_right('', 17)                            # 864-880: Beneficiary City (17 chars)
    record += pad_right('', 3)                             # 881-883: Beneficiary Country Code (3 chars)
    record += pad_right('', 15)                            # 884-898: Beneficiary Postal Code (15 chars)
    record += pad_right(row['Email'][:50], 50)             # 899-948: Email Address (50 chars)
    record += pad_right('', 20)                            # 949-968: Facsimile Number (20 chars)
    record += pad_right('', 35)                            # 969-1003: Payer's Name Line 1 (35 chars)
    record += pad_right('', 35)                            # 1004-1038: Payer's Name Line 2 (35 chars)
    record += pad_right('', 17)                            # 1039-1055: Filler (17 chars)
    
    return record[:1055]  # Ensure exactly 1055 chars

def create_trailer_record(total_amount, total_count, hash_total):
    """Create Type 9 - Batch Trailer Record (1055 chars)"""
    record = ''
    record += '9'                                          # 1: Record Type
    record += format_amount(total_amount)                  # 2-19: Total Amount (18 chars)
    record += pad_left_zero(total_count, 7)                # 20-26: Total Number of Transactions (7 chars)
    record += hash_total                                   # 27-42: Hash Total (16 chars)
    record += pad_right('', 1013)                          # 43-1055: Filler (1013 chars)
    
    return record[:1055]  # Ensure exactly 1055 chars

def convert_excel_to_uob(input_file, output_file):
    """Main conversion function"""
    # Read Excel file
    df = pd.read_excel(input_file)
    
    # Clean data - remove rows with NaN in critical columns
    df = df.dropna(subset=['Name of Recipient ', 'Bank Account Number ', 'Amount'])
    
    # Get dates
    today = datetime.now()
    creation_date_long = today.strftime('%Y%m%d')  # YYYYMMDD
    value_date = creation_date_long  # Same as creation date
    
    # Generate filename in UGAIddmmNN.txt format
    ddmm = today.strftime('%d%m')
    file_name = f'UGAI{ddmm}00'  # Using 00 as sequence number
    
    # If output_file not specified or is default, use standard naming
    if output_file == 'output.TXT':
        output_file = f'{file_name}.txt'
    
    # Build records
    header_record = create_header_record(file_name, creation_date_long, value_date)
    
    detail_records = []
    total_amount = 0
    
    for idx, row in df.iterrows():
        seq_num = idx + 1
        detail_record = create_detail_record(row, seq_num)
        detail_records.append(detail_record)
        total_amount += float(row['Amount'])
    
    # Calculate hash total
    hash_total = calculate_hash_total(header_record, detail_records)
    
    # Create trailer record
    trailer_record = create_trailer_record(total_amount, len(detail_records), hash_total)
    
    # Write to file
    with open(output_file, 'wb') as f:
        # Write header
        f.write((header_record + '\r\n').encode('ascii'))
        
        # Write detail records
        for record in detail_records:
            f.write((record + '\r\n').encode('ascii'))
        
        # Write trailer
        f.write((trailer_record + '\r\n').encode('ascii'))
    
    print(f"Conversion complete!")
    print(f"Output file: {output_file}")
    print(f"Total records: {len(detail_records)}")
    print(f"Total amount: SGD {total_amount:,.2f}")
    print(f"Hash total: {hash_total}")
    
    # Verify record lengths
    with open(output_file, 'rb') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            record_len = len(line) - 2  # Subtract CRLF
            if record_len != 1055:
                print(f"WARNING: Line {i+1} has {record_len} chars, expected 1055")

def main():
    parser = argparse.ArgumentParser(description='Convert Excel to UOB FAST/GIRO format with Payment Advice')
    parser.add_argument('input', help='Input Excel file path')
    parser.add_argument('-o', '--output', help='Output TXT file path', 
                       default='output.TXT')
    
    args = parser.parse_args()
    
    try:
        convert_excel_to_uob(args.input, args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()