import pandas as pd
import os
from datetime import datetime

def process_tds(zfi071_file, zfitdsrep_file, output_folder):
    try:
        # -----------------------
        # Load Excel files
        # -----------------------
        zfi071_df = pd.read_excel(zfi071_file)
        zfitdsrep_df = pd.read_excel(zfitdsrep_file)

        # -----------------------
        # Clean & standardize
        # -----------------------
        for df in (zfi071_df, zfitdsrep_df):
            df["Company Code"] = (
                df["Company Code"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )
            df["Vendor"] = (
                df["Vendor"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                .str.lstrip("0")
            )
            df["Document No."] = (
                df["Document No."]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
            )

        # -----------------------
        # Create Unique Key
        # -----------------------
        zfi071_df["Unique_Key"] = (
            zfi071_df["Company Code"]
            + "-"
            + zfi071_df["Vendor"]
            + "-"
            + zfi071_df["Document No."]
        )

        zfitdsrep_df["Unique_Key"] = (
            zfitdsrep_df["Company Code"]
            + "-"
            + zfitdsrep_df["Vendor"]
            + "-"
            + zfitdsrep_df["Document No."]
        )

        # -----------------------
        # Merge PO mapping
        # -----------------------
        po_mapping = zfi071_df[["Unique_Key", "PO No.", "Item Text"]].drop_duplicates()
        merged_df = pd.merge(
            zfitdsrep_df, po_mapping, on="Unique_Key", how="left"
        )

        filtered_df = merged_df[
            merged_df["PO No._x"].notna()
            & (merged_df["PO No._x"].astype(str).str.strip() != "")
        ]

        # -----------------------
        # TDS2 filtering logic
        # -----------------------
        df = filtered_df.copy()
        df = df[df["TDS Section"] == "194C"]
        df = df[~df["Pan No"].astype(str).str[3].isin(["P", "H"])]
        df = df[df["TDS Rate"] < 2]

        # -----------------------
        # Save output to uploads
        # -----------------------
        os.makedirs(output_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        final_output = os.path.join(
            output_folder,
            f"Final_Output_TDS2_{timestamp}.xlsx"
        )

        df.to_excel(final_output, index=False)

        # 🔑 IMPORTANT: return FILE PATH
        return final_output

    except Exception as e:
        raise Exception(str(e))
