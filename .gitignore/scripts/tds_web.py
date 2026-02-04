import pandas as pd
import os
from datetime import datetime
import logging

def process_tds(zfi071_file, zfitdsrep_file, output_folder=None):
    try:
        # Load Excel files
        zfi071_df = pd.read_excel(zfi071_file)
        zfitdsrep_df = pd.read_excel(zfitdsrep_file)

        # Clean and standardize columns
        for df in [zfi071_df, zfitdsrep_df]:
            df['Company Code'] = df['Company Code'].astype(str).str.replace('.0', '', regex=False).str.strip()
            df['Vendor'] = df['Vendor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.lstrip('0')
            df['Document No.'] = df['Document No.'].astype(str).str.replace('.0', '', regex=False).str.strip()

        # Create Unique_Key
        zfi071_df['Unique_Key'] = zfi071_df['Company Code'] + '-' + zfi071_df['Vendor'] + '-' + zfi071_df['Document No.']
        zfitdsrep_df['Unique_Key'] = zfitdsrep_df['Company Code'] + '-' + zfitdsrep_df['Vendor'] + '-' + zfitdsrep_df['Document No.']

        # Merge
        po_mapping = zfi071_df[['Unique_Key', 'PO No.', 'Item Text']].drop_duplicates()
        merged_df = pd.merge(zfitdsrep_df, po_mapping, on='Unique_Key', how='left')

        filtered_df = merged_df[merged_df['PO No._x'].notna() & (merged_df['PO No._x'].astype(str).str.strip() != '')]

        # Step 2 filtering
        df = filtered_df.copy()
        df = df[df['TDS Section'] == '194C']
        df = df[~df['Pan No'].astype(str).str[3].isin(['P', 'H'])]
        df = df[df['TDS Rate'] < 2]

        # ✅ Always save output in Windows Downloads folder
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        # ✅ Add timestamp in format: DD-MM-YYYY_HH-MM (24-hour format)
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        final_output = os.path.join(downloads_folder, f"Final_Output_TDS2_{timestamp}.xlsx")

        df.to_excel(final_output, index=False)

        return f"✅ Process Completed Successfully!<br>File saved to: <b>{final_output}</b>"

    except Exception as e:
        return f"❌ Error: {e}"
