import pandas as pd
import os
from datetime import datetime

def process_duplicate(purchase_register_file, output_folder=None):
    try:
        # === Load file ===
        if purchase_register_file.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(purchase_register_file)
        elif purchase_register_file.endswith('.csv'):
            df = pd.read_csv(purchase_register_file)
        else:
            raise Exception("Unsupported file format! Please upload Excel or CSV file.")

        # === Check necessary columns ===
        required_cols = ["Document Type", "Vendor", "Amount in LC", "Reference", "Document No"]
        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Missing required column: '{col}'")

        # === Filter only RE ===
        df = df[df["Document Type"] == "RE"]

        # === Create concatenated key ===
        df["Concatenated_Key"] = (
            df["Vendor"].astype(str).str.strip() +
            df["Amount in LC"].astype(str).str.strip() +
            df["Reference"].astype(str).str.strip()
        )

        # === Find duplicates where Journal Entry differs ===
        mask = df.groupby("Concatenated_Key")["Document No"].transform("nunique") > 1
        duplicate_rows = df[mask]

        # === Save ONLY duplicates to Downloads ===
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        duplicates_output = os.path.join(downloads_folder, f"Duplicates_Output_{timestamp}.xlsx")

        duplicate_rows.to_excel(duplicates_output, index=False)

        return (
            f"✅ Process Completed Successfully!<br><br>"
            f"📁 <b>Duplicates File Saved At:</b><br>{duplicates_output}"
        )

    except Exception as e:
        return f"❌ Error: {str(e)}"
