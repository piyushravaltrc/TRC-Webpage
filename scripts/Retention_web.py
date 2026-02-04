import pandas as pd
import os
from datetime import datetime

# def process_retention(invoice_path, vendor_path, retention_path):
def process_retention(invoice_path, vendor_path, retention_path, output_folder):
    try:
        # Step 1: Load Invoice Dump
        zdcctrk_df = pd.read_excel(invoice_path)
        zdcctrk_df.columns = zdcctrk_df.columns.str.replace('\xa0', ' ', regex=False)

        required_columns = [
            "Vendor Number", "Company Code", "Purchasing Document Number", "Accounting Document Number",
            "Value of Checklist", "Vendor Name", "Status of checklist", "Accounting Document Type",
            "Reference Document Number", "Invoice Number"
        ]
        final_filtered = zdcctrk_df[required_columns]

        # Step 2: Filter for RE + CREATED
        filtered_data = final_filtered[
            (final_filtered["Accounting Document Type"] == "RE") &
            (final_filtered["Status of checklist"] == "CREATED")
        ].rename(columns={"Vendor Number": "Vendor Code"})

        # Step 3: Pivot table
        pivot_table = pd.pivot_table(
            filtered_data,
            values="Value of Checklist",
            index=[
                "Company Code", "Vendor Code", "Purchasing Document Number",
                "Accounting Document Number", "Vendor Name", "Accounting Document Type",
                "Status of checklist", "Invoice Number"
            ],
            aggfunc="sum",
            fill_value=0
        ).reset_index()

        # Step 4: Vendor Ledger
        vendor_df = pd.read_excel(vendor_path)
        vendor_df = vendor_df[[
            "Document Number", "Reference", "Document Type",
            "Amount in local currency", "Text", "Company Code", "Account Name", "Vendor"
        ]]
        vendor_df.rename(columns={"Reference": "Invoice Number"}, inplace=True)

        # Step 5: Filter Retention related entries
        keywords = ["RETENTION", "Retention money", "RET Retention"]
        text_filter = vendor_df["Text"].str.contains('|'.join(keywords), case=False, na=False)
        document_type_filter = vendor_df["Document Type"].str.strip().eq("KG")
        filtered_vendor = vendor_df[text_filter & (document_type_filter | ~document_type_filter)]

        # Step 6: Merge with pivot
        merged_df = pivot_table.merge(
            filtered_vendor[["Invoice Number", "Amount in local currency"]],
            how="left", on="Invoice Number"
        )
        merged_df["Amount in local currency"].fillna("#N/A", inplace=True)
        merged_df.rename(columns={
            "Amount in local currency": 
            "Retention amount deducted as per Vendor ledger(FBL1N) (SYSTEM)"
        }, inplace=True)

        # Remove negative values
        merged_df = merged_df[
            ~merged_df["Retention amount deducted as per Vendor ledger(FBL1N) (SYSTEM)"]
            .apply(lambda x: isinstance(x, (int, float)) and x < 0)
        ]

        # Step 7: Add Retention % from Retention terms file
        zfiart_df = pd.read_excel(retention_path)

        merged_df = merged_df.merge(
            zfiart_df[["PO Number", "Retention %"]]
            .rename(columns={"Retention %": "Retention %  As per ZFIART11017 (SYSTEM)"}),
            how="left",
            left_on="Purchasing Document Number",
            right_on="PO Number"
        ).drop(columns=["PO Number"], errors="ignore")

        # Step 8: Calculate Retention amount (MANUAL)
        merged_df["Value of Checklist"] = pd.to_numeric(merged_df["Value of Checklist"], errors="coerce")
        merged_df["Retention %  As per ZFIART11017 (SYSTEM)"] = pd.to_numeric(
            merged_df["Retention %  As per ZFIART11017 (SYSTEM)"], errors="coerce"
        )

        merged_df["Retention amount as per checklist value (Manual)"] = (
            merged_df["Value of Checklist"] * 
            (merged_df["Retention %  As per ZFIART11017 (SYSTEM)"] / 100)
        )

        # Step 9: Calculate difference
        merged_df["Retention amount deducted as per Vendor ledger(FBL1N) (SYSTEM)"] = pd.to_numeric(
            merged_df["Retention amount deducted as per Vendor ledger(FBL1N) (SYSTEM)"], errors="coerce"
        )

        merged_df["Retention amount diff"] = (
            merged_df["Retention amount deducted as per Vendor ledger(FBL1N) (SYSTEM)"] -
            merged_df["Retention amount as per checklist value (Manual)"]
        ).round(3)

        # Fill NA values in difference
        mask_na_diff = merged_df["Retention amount diff"].isna()
        merged_df.loc[mask_na_diff, "Retention amount diff"] = -merged_df.loc[
            mask_na_diff, "Retention amount as per checklist value (Manual)"
        ]

        # Step 10: Final remark
        def get_remark(diff):
            if diff == 0:
                return "No Amount Diff"
            elif diff < 0:
                return "Short amount deducted"
            elif diff > 0:
                return "Excess amount deducted"
            return ""

        merged_df["Final remark"] = merged_df["Retention amount diff"].apply(get_remark)

        # SAVE FINAL OUTPUT IN DOWNLOADS
        # downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        # os.makedirs(downloads_folder, exist_ok=True)

        # timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        # final_output = os.path.join(downloads_folder, f"final_Retention_output_with_final_remark_{timestamp}.xlsx")
        os.makedirs(output_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        final_output = os.path.join(
            output_folder,
            f"final_Retention_output_with_final_remark_{timestamp}.xlsx"
        )

        merged_df.to_excel(final_output, index=False)

        # return f"✅ Process Completed Successfully!<br>File saved to: <b>{final_output}</b>"
        return final_output

    except Exception as e:
        raise Exception(f"Processing Error: {str(e)}")
