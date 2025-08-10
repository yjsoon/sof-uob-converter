# SOF UOB Payment File Generator

A Python utility to convert Excel spreadsheets containing scholarship recipient data into UOB FAST/GIRO bulk payment format for the Singapore Olympic Foundation (SOF).

🌐 **[Try the Web App](#web-application)** | 💻 **[Use CLI](#command-line-usage)** | 🚀 **[Deploy Your Own](#deployment)**

## Overview

This tool transforms Excel files with scholarship recipient information into the specific TXT format required by UOB's bulk payment system, following the UOB FAST/GIRO Format Specification v4.8.

## Features

- Converts Excel data to UOB FAST/GIRO format with payment advice
- Supports multiple Singapore banks (DBS, OCBC, UOB, Maybank, etc.)
- Automatic hash calculation for file integrity
- Email notification support for recipients
- Fixed-width ASCII format compliance (1055 characters per record)
- Comprehensive validation and error checking

## Requirements

- Python 3.6+
- pandas library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sof-uob-generator.git
cd sof-uob-generator
```

2. Install dependencies:
```bash
pip install pandas openpyxl
```

## Important Security Notice

⚠️ **NEVER commit real recipient data to version control!**

- The `inputs/` folder is gitignored to protect sensitive bank account information
- The `outputs/` folder is gitignored to protect generated payment files
- Use `inputs/template.xlsx` as a reference for the required Excel format
- Keep all real data files in the `inputs/` folder only

## Web Application

### 🌐 Quick Start (Hosted Version)

Visit the deployed web app at: *[To be deployed on Streamlit Community Cloud]*

### 💻 Run Locally

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit app:
```bash
streamlit run app.py
```

3. Open your browser to `http://localhost:8501`

### Features
- User-friendly web interface
- Customizable organization details
- Excel file upload with preview
- Instant conversion and download
- No data stored on server

## Command Line Usage

Basic usage:
```bash
python3 convert_to_uob.py inputs/2025-primary.xlsx
```

Specify output file:
```bash
python3 convert_to_uob.py inputs/2025-primary.xlsx -o output.TXT
```

The script will generate a file named `UGAIddmmNN.txt` (where ddmm is the current date and NN is a sequence number).

## Input Excel Format

The Excel file must contain the following columns:
- `No` - Sequential number
- `Name of Recipient ` - Full name (note the trailing space)
- `Email` - Recipient's email address
- `Bank` - Bank name with code (e.g., "DBS/POSB - 7171")
- `Bank Account Name` - Name on the bank account
- `Bank Account Number ` - Account number (note the trailing space)
- `Description` - Payment description
- `Amount` - Payment amount in SGD

## Output Format

The generated TXT file contains:
- **Type 1 Record**: Batch header with originator details
- **Type 2 Records**: Payment instructions for each recipient
- **Type 9 Record**: Batch trailer with totals and hash

Each record is exactly 1055 characters wide with CRLF line endings.

## Supported Banks

| Bank | Code | BIC |
|------|------|-----|
| DBS/POSB | 7171 | DBSSSGSGXXX |
| OCBC | 7339 | OCBCSGSGXXX |
| UOB | 7375 | UOVBSGSGXXX |
| Maybank | 7302 | MBBESGSGXXX |
| Standard Chartered | 9496 | SCBLSGSGXXX |
| HSBC | 7232 | HSBCSGSGXXX |
| Citibank | 7214 | CITISGSGXXX |
| Bank of China | 7366 | BKCHSGSGXXX |

## File Structure

```
sof-uob-generator/
├── convert_to_uob.py       # Main conversion script
├── inputs/                 # Input Excel files (gitignored for security)
│   ├── .gitkeep           # Preserves folder structure
│   └── template.xlsx      # Template file with dummy data
├── outputs/               # Output TXT files (gitignored for security)
│   └── .gitkeep          # Preserves folder structure
├── docs/                  # Documentation and specifications
│   ├── Format Specification Guide Bulk FAST_GIRO Format Specification v4.8.pdf
│   └── ParameterTable.xlsx # Bank code reference table
├── README.md             # This file
└── CLAUDE.md            # Development documentation
```

## Technical Details

### Record Structure
- All records are fixed-width ASCII text
- Each record is exactly 1055 characters
- Text fields are right-padded with spaces
- Numeric fields are left-padded with zeros
- Amounts are in cents (multiply by 100) with 18 digits

### Payment Details
- Service Type: NORMAL (for standard FAST payments)
- Processing Mode: I (for immediate FAST processing)
- Purpose Code: OTHR (other payments)
- Payment Type: P (for payments)

### Hash Calculation
The hash total is calculated according to UOB's specification:
1. Sum ASCII values of specific header fields
2. Process each detail record with position-based weighting
3. Include payment type code multiplier
4. Generate 16-digit hash for trailer record

## Troubleshooting

### Common Issues

1. **Excel columns not found**: Ensure column names match exactly (including trailing spaces)
2. **Bank code not recognized**: Check that the bank name matches the supported format
3. **Invalid amounts**: Amounts must be numeric values without currency symbols
4. **Record length errors**: The script validates all records are exactly 1055 characters

### Validation

The script automatically:
- Validates record lengths
- Removes rows with missing critical data
- Calculates hash totals for integrity
- Reports total amount and record count

## Deployment

### Deploy to Streamlit Community Cloud (Recommended - FREE)

1. **Fork or push this repository** to your GitHub account

2. **Sign up** at [share.streamlit.io](https://share.streamlit.io) using your GitHub account

3. **Deploy the app**:
   - Click "New app"
   - Select your repository: `yourusername/sof-uob-converter`
   - Branch: `main`
   - Main file path: `app.py`
   - Click "Deploy"

4. **Your app will be available at**: `https://yourusername-sof-uob-converter.streamlit.app`

### Alternative Deployment Options

#### Netlify (with Streamlit)
While Netlify doesn't natively support Python apps, you can use it with Streamlit via GitHub Actions:
1. Set up GitHub Actions to build and deploy
2. Use Streamlit's static export feature
3. More complex setup required

#### Vercel
Similar limitations as Netlify - requires serverless function setup for Python.

#### Other Free Options
- **Render.com**: Free tier with 750 hours/month
- **Railway.app**: $5 credit/month free tier
- **Fly.io**: Free tier with 3 shared VMs
- **Hugging Face Spaces**: Free Streamlit hosting

### Why Streamlit Community Cloud?
- ✅ **100% Free** - No credit card required
- ✅ **Easy deployment** - Just connect GitHub
- ✅ **Auto-redeploy** - Updates when you push to GitHub
- ✅ **Custom domain** support
- ✅ **No time limits** or usage restrictions
- ✅ **Built for Streamlit** apps specifically

## Development

For development guidelines and technical documentation, see [CLAUDE.md](CLAUDE.md).

## License

This project is proprietary software for the Singapore Olympic Foundation.

## Support

For issues or questions, please contact the SOF IT department.