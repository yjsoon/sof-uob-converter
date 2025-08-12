#!/usr/bin/env python3
"""
Streamlit Web App for UOB FAST/GIRO Payment File Generator
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io
import base64

# Import conversion functions from our existing module
from convert_to_uob import (
    BANK_MAPPING,
    pad_right,
    pad_left_zero,
    format_amount,
    compute_field_check_summary,
    calculate_hash_total,
    create_detail_record,
    create_trailer_record
)

def create_header_record_custom(file_name, creation_date_long, value_date, org_name, org_account, org_bic, customer_ref, processing_mode='B'):
    """Create Type 1 - Batch Header Record with custom organization details
    
    Args:
        processing_mode: 'B' for Normal GIRO (default), 'I' for FAST GIRO
    """
    record = ''
    
    # Build header according to exact spec positions
    record += '1'                                          # 1: Record Type
    record += pad_right(file_name[:10], 10)                # 2-11: File Name (10 chars)
    record += 'P'                                          # 12: Payment Type (P for Payment)
    record += pad_right('NORMAL', 10)                      # 13-22: Service Type (10 chars)
    record += processing_mode                              # 23: Processing Mode (B for Normal, I for FAST)
    record += pad_right('', 12)                            # 24-35: Company ID (12 chars) - conditional
    record += pad_right(org_bic, 11)                       # 36-46: Originating BIC (11 chars)
    record += 'SGD'                                        # 47-49: Currency (3 chars)
    record += pad_right(org_account, 34)                   # 50-83: Originating Account Number (34 chars)
    record += pad_right(org_name, 140)                     # 84-223: Originating Account Name (140 chars)
    record += creation_date_long                           # 224-231: File Creation Date YYYYMMDD (8 chars)
    record += value_date                                   # 232-239: Value Date YYYYMMDD (8 chars)
    record += pad_right('', 140)                           # 240-379: Ultimate Originating Customer (140 chars)
    record += pad_right(customer_ref, 16)                  # 380-395: Bulk Customer Reference (16 chars)
    record += pad_right('', 10)                            # 396-405: Software Label (10 chars)
    record += pad_right('', 105)                           # 406-510: Payment Advice Header Line 1 (105 chars)
    record += pad_right('', 105)                           # 511-615: Payment Advice Header Line 2 (105 chars)
    record += pad_right('', 440)                           # 616-1055: Filler (440 chars)
    
    return record[:1055]  # Ensure exactly 1055 chars

def process_excel_to_uob(df, org_name, org_account, org_bic, customer_ref, payment_desc, processing_mode='B', value_date_override=None):
    """Process Excel dataframe to UOB format with custom parameters
    
    Args:
        processing_mode: 'B' for Normal GIRO (default), 'I' for FAST GIRO
    """
    
    # Clean data - remove rows with NaN in critical columns and filter out total/summary rows
    df = df.dropna(subset=['Name of Recipient ', 'Bank Account Number ', 'Amount'])
    # Also remove rows where 'No' is NaN (likely total rows)
    df = df.dropna(subset=['No'])
    
    # Get dates
    if value_date_override:
        specific_date = value_date_override
    else:
        specific_date = datetime.now()
    
    creation_date_long = specific_date.strftime('%Y%m%d')
    value_date = creation_date_long
    
    # Generate filename in UGAIddmmNN.txt format
    ddmm = specific_date.strftime('%d%m')
    file_name = f'UGAI{ddmm}00'
    
    # Build records
    header_record = create_header_record_custom(
        file_name, creation_date_long, value_date,
        org_name, org_account, org_bic, customer_ref, processing_mode
    )
    
    detail_records = []
    total_amount = 0
    
    for idx, row in df.iterrows():
        seq_num = idx + 1
        # Modify the payment description in the row
        row_copy = row.copy()
        # Update the detail record creation to use custom payment description
        detail_record = create_detail_record(row_copy, seq_num)
        # Replace the hardcoded "SOFPLS SCHOLARSHIP" with custom description
        detail_record = detail_record[:281] + pad_right(payment_desc, 140) + detail_record[421:]
        detail_records.append(detail_record)
        total_amount += float(row['Amount'])
    
    # Calculate hash total
    hash_total = calculate_hash_total(header_record, detail_records)
    
    # Create trailer record
    trailer_record = create_trailer_record(total_amount, len(detail_records), hash_total)
    
    # Build output content
    output_lines = []
    output_lines.append(header_record + '\r\n')
    for record in detail_records:
        output_lines.append(record + '\r\n')
    output_lines.append(trailer_record + '\r\n')
    
    # Join all lines
    output_content = ''.join(output_lines)
    
    return output_content, file_name, total_amount, len(detail_records), hash_total

# Streamlit App
st.set_page_config(
    page_title="UOB Payment File Generator",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 UOB FAST/GIRO Payment File Generator")
st.markdown("Convert Excel files to UOB bulk payment format (v4.8 specification)")

# Create two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📋 Organisation Details")
    
    with st.form("org_details"):
        org_name = st.text_input(
            "Organisation Name",
            value="SINGAPORE OLYMPIC FOUNDATION",
            max_chars=140,
            help="Name of the originating organisation (max 140 characters)"
        )
        
        org_account = st.text_input(
            "Originating Account Number",
            value="3663050778",
            max_chars=34,
            help="Your organisation's bank account number (max 34 characters)"
        )
        
        org_bic = st.text_input(
            "Originating Bank BIC",
            value="UOVBSGSGXXX",
            max_chars=11,
            help="Your bank's SWIFT/BIC code (11 characters)"
        )
        
        customer_ref = st.text_input(
            "Bulk Customer Reference",
            value="SOFPLSAWARD",
            max_chars=16,
            help="Reference code for this batch (max 16 characters)"
        )
        
        payment_desc = st.text_input(
            "Payment Description",
            value="SOFPLS SCHOLARSHIP",
            max_chars=140,
            help="Description that appears on receipts (max 140 characters)"
        )
        
        # Processing mode selection
        processing_mode = st.selectbox(
            "Processing Mode",
            options=['B', 'I'],
            format_func=lambda x: "Normal GIRO (Standard charges)" if x == 'B' else "FAST GIRO (Higher charges, faster processing)",
            index=0,  # Default to 'B' (Normal GIRO)
            help="Select the processing mode for payments"
        )
        
        # Value date selection
        value_date = st.date_input(
            "Value Date",
            datetime.now(),
            help="The date when the payment should be processed"
        )
        
        form_submitted = st.form_submit_button("Apply Settings", type="primary")

with col2:
    st.header("📁 Upload Excel File")
    
    # Show template info
    with st.expander("📝 Excel Format Requirements"):
        st.markdown("""
        Your Excel file must contain these columns (with exact names including spaces):
        - `No` - Sequential number
        - `Name of Recipient ` - Full name (note trailing space)
        - `Email` - Recipient's email
        - `Bank` - Bank name with code (e.g., "DBS/POSB - 7171")
        - `Bank Account Name` - Name on bank account
        - `Bank Account Number ` - Account number (note trailing space)
        - `Description` - Payment description
        - `Amount` - Payment amount in SGD
        """)
        
        st.markdown("**Supported Banks:**")
        bank_list = [f"- {bank}" for bank in BANK_MAPPING.keys()]
        st.markdown("\n".join(bank_list))
    
    uploaded_file = st.file_uploader(
        "Choose an Excel file",
        type=['xlsx', 'xls'],
        help="Upload your payment data in Excel format"
    )
    
    if uploaded_file is not None:
        try:
            # Read the Excel file
            df = pd.read_excel(uploaded_file)
            
            # Show preview
            st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
            
            with st.expander("Preview Data (first 5 rows)"):
                # Hide sensitive columns in preview
                preview_df = df.head().copy()
                if 'Bank Account Number ' in preview_df.columns:
                    preview_df['Bank Account Number '] = preview_df['Bank Account Number '].astype(str).str[:3] + '***'
                if 'Email' in preview_df.columns:
                    preview_df['Email'] = preview_df['Email'].str.replace(r'(.{3}).*(@.*)', r'\1***\2', regex=True)
                st.dataframe(preview_df)
            
            # Show statistics with custom styling
            col2_1, col2_2, col2_3 = st.columns(3)
            
            # Add custom CSS for smaller metric text
            st.markdown("""
            <style>
            [data-testid="metric-container"] {
                margin: -5px 0;
            }
            [data-testid="metric-container"] > div {
                padding: 5px 10px;
            }
            [data-testid="metric-container"] [data-testid="stMetricValue"] {
                font-size: 1.8rem;
            }
            [data-testid="metric-container"] [data-testid="stMetricLabel"] {
                font-size: 0.9rem;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Filter out total/summary rows (rows with NaN in 'No' column)
            df_clean = df.dropna(subset=['No', 'Name of Recipient ', 'Amount'])
            
            with col2_1:
                st.metric("Total Records", len(df_clean))
            with col2_2:
                total_amt = df_clean['Amount'].sum()
                # Format large numbers more compactly
                if total_amt >= 1000:
                    st.metric("Total Amount", f"SGD {total_amt/1000:.1f}K")
                else:
                    st.metric("Total Amount", f"SGD {total_amt:,.2f}")
            with col2_3:
                st.metric("Banks", df_clean['Bank'].nunique())
            
            # Process button
            if st.button("🚀 Generate UOB File", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    try:
                        # Process the file
                        output_content, filename, total_amount, record_count, hash_total = process_excel_to_uob(
                            df, 
                            org_name, 
                            org_account, 
                            org_bic, 
                            customer_ref, 
                            payment_desc,
                            processing_mode,
                            datetime.combine(value_date, datetime.min.time())
                        )
                        
                        # Success message
                        st.success("✅ File generated successfully!")
                        
                        # Add custom CSS for smaller result metrics
                        st.markdown("""
                        <style>
                        [data-testid="column"] [data-testid="metric-container"] [data-testid="stMetricValue"] {
                            font-size: 1.5rem !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Show results
                        result_col1, result_col2, result_col3 = st.columns(3)
                        with result_col1:
                            st.metric("Records Processed", record_count)
                        with result_col2:
                            st.metric("Hash Total", hash_total)
                        with result_col3:
                            st.metric("Output Filename", f"{filename}.txt")
                        
                        # Download button
                        st.download_button(
                            label="📥 Download UOB File",
                            data=output_content.encode('ascii'),
                            file_name=f"{filename}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.exception(e)
                        
        except Exception as e:
            st.error(f"❌ Error reading Excel file: {str(e)}")
            st.info("Please ensure your Excel file has the correct format and column names.")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    <small>
    UOB FAST/GIRO Format v4.8 | 
    <a href="https://github.com/yjsoon/sof-uob-converter" target="_blank">GitHub</a> | 
    Each record: 1055 characters
    </small>
</div>
""", unsafe_allow_html=True)

# Sidebar with instructions
with st.sidebar:
    st.header("📖 How to Use")
    st.markdown("""
    1. **Fill in your organisation details** in the form
    2. **Upload your Excel file** with payment data
    3. **Review the preview** to ensure data is correct
    4. **Click Generate** to create the UOB file
    5. **Download** the generated TXT file
    
    ---
    
    ### 🔒 Security Note
    All processing happens in your browser session. 
    No data is stored on the server.
    """)