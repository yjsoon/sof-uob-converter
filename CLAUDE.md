# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a UOB FAST/GIRO bulk payment file generator for the Singapore Olympic Foundation (SOF) scholarship payments. It converts Excel spreadsheets containing recipient information into the specific TXT format required by UOB's bulk payment system.

## Core Functionality

The main conversion script `convert_to_uob.py` transforms Excel files with scholarship recipient data into UOB's FAST/GIRO format following the specification in `docs/Format Specification Guide Bulk FAST_GIRO Format Specification v4.8.pdf`.

### Input Excel Format
Excel files must contain these columns:
- `No` - Sequential number
- `Name of Recipient ` - Full name (note trailing space in column name)
- `Email` - Recipient's email for payment notification
- `Bank` - Bank name with code (e.g., "DBS/POSB - 7171")
- `Bank Account Name` - Name on bank account
- `Bank Account Number ` - Account number (note trailing space in column name)
- `Description` - Payment description
- `Amount` - Payment amount in SGD

### Output Format
The script generates a fixed-width ASCII text file with:
- **Type 1 Record**: Batch header with originator details (Singapore Olympic Foundation)
- **Type 2 Records**: Payment instructions for each recipient (with payment advice)
- **Type 9 Record**: Batch trailer with totals and hash

Note: Type 4 records (add-on details) are not currently implemented as they are optional and not shown in the expected output.

## Commands

### Convert Excel to UOB format
```bash
python3 convert_to_uob.py inputs/2025-primary.xlsx
```

### Specify custom output file
```bash
python3 convert_to_uob.py inputs/2025-primary.xlsx -o custom_output.TXT
```

### Install dependencies
```bash
pip install pandas openpyxl
```

## Bank Code Mapping

The system maps Excel bank names to SWIFT BIC codes:
- DBS/POSB - 7171 → DBSSSGSGXXX
- OCBC - 7339 → OCBCSGSGXXX  
- UOB - 7375 → UOVBSGSGXXX
- Maybank - 7302 → MBBESGSGXXX
- Standard Chartered - 9496 → SCBLSGSGXXX
- HSBC - 7232 → HSBCSGSGXXX
- Citibank - 7214 → CITISGSGXXX
- Bank of China - 7366 → BKCHSGSGXXX

## Key Implementation Details

### Fixed Field Widths
- All records are exactly 1055 characters wide (with payment advice)
- Text fields are right-padded with spaces
- Numeric fields are left-padded with zeros
- Amounts are in cents (multiply by 100) with 18 digits

### Date Formats
- Short dates: YYMMDD (6 digits)
- Long dates: YYYYMMDD (8 digits)
- Uses current date for both creation and value dates

### Payment Details
- Fixed description: "SOFPLS SCHOLARSHIP"
- Purpose code: "OTHR"
- Service Type: "NORMAL" for standard FAST payments
- Processing Mode: "I" for immediate FAST processing
- Payment Type: "P" for payments
- Email notifications enabled for all recipients
- End-to-End ID: Generated as REF0001, REF0002, etc.

## Testing Considerations

When modifying the conversion:
1. Ensure all records maintain exactly 1055 character width
2. Verify bank code mappings for new banks
3. Test with Excel files containing special characters in names
4. Confirm amounts are correctly converted to cents (18 digits)
5. Check that email addresses are properly truncated at 50 characters
6. Verify hash calculation matches UOB specification (Appendix 4)
7. Validate field positions match specification exactly

## Common Tasks

### Add new bank mapping
Edit `BANK_MAPPING` dictionary in `convert_to_uob.py`

### Change originator details
Modify `create_header_record()` function - currently hardcoded for Singapore Olympic Foundation

### Adjust payment description
Update the description in `create_detail_record()` and `create_addon_record()` functions