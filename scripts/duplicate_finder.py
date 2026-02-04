import pandas as pd
import os
from datetime import datetime

def process_duplicate(purchase_register_file, output_folder):
    # Load file
    if purchase_register_file.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(purchase_register_file)
    elif purchase_register_file.endswith('.csv'):
        df = pd.read_csv(purchase_register_file)
    else:
        raise Exception("Unsupported file format")

    required_cols = ["Document Type", "Vendor", "Amount in LC", "Reference", "Document No"]
    for col in required_cols:
        if col not in df.columns:
            raise Exception(f"Missing required column: {col}")

    df = df[df["Document Type"] == "RE"]

    df["Concatenated_Key"] = (
        df["Vendor"].astype(str).str.strip() +
        df["Amount in LC"].astype(str).str.strip() +
        df["Reference"].astype(str).str.strip()
    )

    mask = df.groupby("Concatenated_Key")["Document No"].transform("nunique") > 1
    duplicate_rows = df[mask]

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
    output_file = os.path.join(output_folder, f"Duplicates_Output_{timestamp}.xlsx")

    duplicate_rows.to_excel(output_file, index=False)

    return output_file
