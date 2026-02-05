import pandas as pd
import os
from datetime import datetime

LOG_FILE = "tds2_log.txt"


def write_log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {message}\n")


def process_tds2(zfi071_file, zfitdsrep_file, output_folder):
    try:
        write_log("TDS2 process started")
        write_log(f"ZFI071 File: {zfi071_file}")
        write_log(f"ZFITDSREP File: {zfitdsrep_file}")

        zfi071_df = pd.read_excel(zfi071_file)
        zfitdsrep_df = pd.read_excel(zfitdsrep_file)

        for df in [zfi071_df, zfitdsrep_df]:
            df["Company Code"] = df["Company Code"].astype(str).str.replace(".0", "", regex=False).str.strip()
            df["Vendor"] = df["Vendor"].astype(str).str.replace(".0", "", regex=False).str.strip().str.lstrip("0")
            df["Document No."] = df["Document No."].astype(str).str.replace(".0", "", regex=False).str.strip()

        zfi071_df["Unique_Key"] = (
            zfi071_df["Company Code"] + "-" +
            zfi071_df["Vendor"] + "-" +
            zfi071_df["Document No."]
        )

        zfitdsrep_df["Unique_Key"] = (
            zfitdsrep_df["Company Code"] + "-" +
            zfitdsrep_df["Vendor"] + "-" +
            zfitdsrep_df["Document No."]
        )

        po_mapping = zfi071_df[["Unique_Key", "PO No.", "Item Text"]].drop_duplicates()

        merged_df = pd.merge(
            zfitdsrep_df,
            po_mapping,
            on="Unique_Key",
            how="left"
        )

        df = merged_df[
            merged_df["PO No._x"].notna() &
            (merged_df["PO No._x"].astype(str).str.strip() != "")
        ]

        df = df[df["TDS Section"] == "194C"]
        df = df[~df["Pan No"].astype(str).str[3].isin(["P", "H"])]
        df = df[df["TDS Rate"] < 2]

        os.makedirs(output_folder, exist_ok=True)

        output_file = os.path.join(
            output_folder,
            f"Final_Output_TDS2_{datetime.now():%d-%m-%Y_%H-%M}.xlsx"
        )

        df.to_excel(output_file, index=False)

        write_log(f"Rows identified: {df.shape[0]}")
        write_log(f"Output file created: {output_file}")
        write_log("TDS2 process completed successfully")

        return output_file

    except Exception as e:
        write_log(f"ERROR: {str(e)}")
        raise Exception(str(e))
