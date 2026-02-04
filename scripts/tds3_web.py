import pandas as pd
import os
from datetime import datetime
import re

def process_tds3(zfi_file, zfit_file):
    """
    TDS3 Processing Function (Flask-friendly message return)
    Args:
        zfi_file (str): Path to ZFI071 Excel file
        zfit_file (str): Path to ZFITDSREP Excel file
    Returns:
        str: HTML-friendly message with output file info or error
    """
    try:
        # --- Step 0: Setup Downloads folder ---
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        # --- Step 1: Load Excel files ---
        zfi_df = pd.read_excel(zfi_file)
        zfit_df = pd.read_excel(zfit_file)

        # --- Step 2: Clean and standardize ---
        for df in [zfi_df, zfit_df]:
            df['Company Code'] = df['Company Code'].astype(str).str.replace('.0', '', regex=False).str.strip()
            df['Vendor'] = df['Vendor'].astype(str).str.replace('.0', '', regex=False).str.strip().str.lstrip('0')
            df['Document No.'] = df['Document No.'].astype(str).str.replace('.0', '', regex=False).str.strip()

        # --- Step 3: Create Unique Key ---
        zfi_df['Unique_Key'] = zfi_df['Company Code'] + '-' + zfi_df['Vendor'] + '-' + zfi_df['Document No.']
        zfit_df['Unique_Key'] = zfit_df['Company Code'] + '-' + zfit_df['Vendor'] + '-' + zfit_df['Document No.']

        # --- Step 4: Merge PO mapping ---
        po_mapping = zfi_df[['Unique_Key', 'PO No.', 'Item Text']].drop_duplicates()
        merged_df = pd.merge(zfit_df, po_mapping, on='Unique_Key', how='left')

        # --- Step 5: Filter blank PO No. ---
        filtered_df = merged_df[merged_df['PO No._x'].notna() & (merged_df['PO No._x'].astype(str).str.strip() != '')]

        # --- Step 6: Remove "rev" in Ref. Docnr ---
        filtered_df = filtered_df[~filtered_df['Ref. Docnr.'].str.contains('rev', case=False, na=False)]

        # --- Step 7: Remove PO No. with same +ve/-ve Base Value summing to 0 ---
        po_value_groups = filtered_df.groupby(['PO No._x', 'Base Value']).size().reset_index(name='count')
        po_value_pivot = po_value_groups.pivot_table(index='PO No._x', columns='Base Value', values='count', fill_value=0)
        po_no_to_remove = []
        for po_no, values in po_value_pivot.iterrows():
            for value in values.index:
                if value > 0 and -value in values.index:
                    if values[value] > 0 and values[-value] > 0:
                        po_no_to_remove.append(po_no)
                        break
        filtered_df = filtered_df[~filtered_df['PO No._x'].isin(po_no_to_remove)]

        # --- Step 8: Remove PO No. with both 194Q and 194C ---
        tds_sections = filtered_df.groupby('PO No._x')['TDS Section'].agg(lambda x: set(x))
        po_no_to_exclude = [po_no for po_no, sections in tds_sections.items() if {'194Q', '194C'}.issubset(sections)]
        filtered_df = filtered_df[~filtered_df['PO No._x'].isin(po_no_to_exclude)]

        # --- Step 9: Filter Item Text for keywords & TDS Rate < 10 ---
        keywords = [
            "prof", "professional", "consultancy", "auditing", "audit", "legal",
            "medical", "engineering", "architecture", "architect", "interior",
            "interior designer", "decoration", "accounting", "accountancy",
            "book keeping", "advertising"
        ]
        filtered_df['Item Text'] = filtered_df['Item Text'].astype(str).str.lower()
        mask = filtered_df['Item Text'].apply(lambda x: any(keyword in x for keyword in keywords))
        mask_tds = filtered_df['TDS Rate'].fillna(0) < 10
        filtered_df = filtered_df[mask & mask_tds]

        # --- Step 10: Remove CN/DN rows ---
        cn_keywords = ["CN", "DN", "CREDIT NOTE", "DEBIT NOTE"]
        pattern = r'\b(?:' + '|'.join(re.escape(keyword) for keyword in cn_keywords) + r')\b'
        filtered_df = filtered_df[~filtered_df['Item Text'].str.contains(pattern, case=False, na=False)]

        # --- Step 11: Save output in Downloads ---
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        output_file = os.path.join(downloads_folder, f"Final_Output_TDS3_{timestamp}.xlsx")
        filtered_df.to_excel(output_file, index=False)

        # ✅ Return message for Flask
        return f"✅ TDS3 Process Completed Successfully!<br>📁 File saved in Downloads:<br>- <b>{os.path.basename(output_file)}</b>"

    except Exception as e:
        return f"❌ Error: {e}"
