import pandas as pd
import os
from datetime import datetime

def process_tds1(zfi071_file, zfitdsrep_file, output_folder=None):
    try:
        # Step 1: Load Excel files
        zfi071_df = pd.read_excel(zfi071_file)
        zfitdsrep_df = pd.read_excel(zfitdsrep_file)

        # Step 2: Clean and standardize Vendor and Company Code
        for df in [zfi071_df, zfitdsrep_df]:
            df['Company Code'] = df['Company Code'].astype(str).str.replace('.0', '', regex=False).str.strip()
            df['Vendor'] = df['Vendor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.lstrip('0')
            df['Document No.'] = df['Document No.'].astype(str).str.replace('.0', '', regex=False).str.strip()

        # Step 3: Create Unique_Key in both dataframes
        zfi071_df['Unique_Key'] = (
            zfi071_df['Company Code'] + '-' +
            zfi071_df['Vendor'] + '-' +
            zfi071_df['Document No.']
        )

        zfitdsrep_df['Unique_Key'] = (
            zfitdsrep_df['Company Code'] + '-' +
            zfitdsrep_df['Vendor'] + '-' +
            zfitdsrep_df['Document No.']
        )

        # Step 4: Create PO mapping from zfi071_df
        po_mapping = zfi071_df[['Unique_Key', 'PO No.', 'Item Text']].drop_duplicates()

        # Step 5: Merge
        merged_df = pd.merge(zfitdsrep_df, po_mapping, on='Unique_Key', how='left')

        # Step 6: Filter out rows with blank or NaN PO No.
        filtered_df = merged_df[
            merged_df['PO No._x'].notna() & (merged_df['PO No._x'].astype(str).str.strip() != '')
        ]

        # Step 7: Find PO numbers with more than one TDS Rate
        tds_counts = filtered_df.groupby("PO No._x")["TDS Rate"].nunique()
        po_multiple_tds = tds_counts[tds_counts > 1].index
        df_multiple_tds = filtered_df[filtered_df["PO No._x"].isin(po_multiple_tds)]

        # ✅ Save only one final output file (in Downloads)
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        final_output = os.path.join(downloads_folder, f"Final_Output_TDS1_{timestamp}.xlsx")
        df_multiple_tds.to_excel(final_output, index=False)

        # ✅ Return message for Flask
        return (
            f"✅ TDS1 Process Completed Successfully!<br>"
            f"📁 File saved in your Downloads folder:<br>"
            f"- <b>{os.path.basename(final_output)}</b>"
        )

    except Exception as e:
        return f"❌ Error: {e}"
