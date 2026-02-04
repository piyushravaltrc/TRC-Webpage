import pandas as pd
import os
from datetime import datetime

def run_tds_rules(uploaded_file, selected_rules):
    """
    Process uploaded Excel file based on selected TDS rules and
    save final output to Downloads folder.

    Parameters:
    uploaded_file : Flask FileStorage object (Excel file)
    selected_rules : list of selected rules like
        ['194C_OVERALL', '194C_INDIVIDUAL', '194H', '194J', '194Q']

    Returns:
    Flask-friendly HTML message with file info
    """
    try:
        # -----------------------
        # Step 1: Read Excel file
        # -----------------------
        df = pd.read_excel(uploaded_file)

        # -----------------------
        # Step 2: Clean/standardize columns
        # -----------------------
        df["Vendor"] = df["Vendor"].astype(str).str.strip()
        df["Document Number"] = df["Document Number"].astype(str).str.strip()
        df["Total Taxable Value"] = pd.to_numeric(df["Total Taxable Value"], errors="coerce").fillna(0)
        df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")

        # -----------------------
        # Step 3: Apply TDS rules
        # -----------------------
        result_frames = []

        # 194C - Overall ₹1,00,000
        if "194C_OVERALL" in selected_rules:
            df_194C = df[df["TDS Section"] == "194C"].sort_values(["Vendor", "Posting Date"]).copy()
            df_194C["Cumulative"] = df_194C.groupby("Vendor")["Total Taxable Value"].cumsum()
            result_frames.append(df_194C[df_194C["Cumulative"] > 100000])

        # 194C - Individual Bill > ₹30,000
        if "194C_INDIVIDUAL" in selected_rules:
            df_194C_ind = df[df["TDS Section"] == "194C"].copy()
            result_frames.append(
                df_194C_ind.groupby("Document Number").filter(lambda x: x["Total Taxable Value"].sum() > 30000)
            )

        # 194H - Bill > ₹20,000
        if "194H" in selected_rules:
            df_194H = df[df["TDS Section"] == "194H"].copy()
            result_frames.append(
                df_194H.groupby("Document Number").filter(lambda x: x["Total Taxable Value"].sum() > 20000)
            )

        # 194J - Bill > ₹50,000
        if "194J" in selected_rules:
            df_194J = df[df["TDS Section"] == "194J"].copy()
            result_frames.append(
                df_194J.groupby("Document Number").filter(lambda x: x["Total Taxable Value"].sum() > 50000)
            )

        # 194Q - Overall ₹50,00,000
        if "194Q" in selected_rules:
            df_194Q = df[df["TDS Section"] == "194Q"].sort_values(["Vendor", "Posting Date"]).copy()
            df_194Q["Cumulative"] = df_194Q.groupby("Vendor")["Total Taxable Value"].cumsum()
            result_frames.append(df_194Q[df_194Q["Cumulative"] > 5000000])

        # -----------------------
        # Step 4: Combine results
        # -----------------------
        final_df = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()

        # -----------------------
        # Step 5: Save to Downloads
        # -----------------------
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads_folder, exist_ok=True)

        # Optional: overwrite previous file instead of timestamp
        # final_output = os.path.join(downloads_folder, "Final_Output_TDS.xlsx")

        # Or use timestamp
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        final_output = os.path.join(downloads_folder, f"Final_Output_TDS_{timestamp}.xlsx")

        final_df.to_excel(final_output, index=False)

        # -----------------------
        # Step 6: Return clean HTML message
        # -----------------------
        filename = os.path.basename(final_output)

        if final_df.empty:
            return (
                f"⚠️ No records matched the selected TDS rules.<br>"
                f"📁 File saved in your Downloads folder:<br>"
                f"- <b>{filename}</b>"
            )
        else:
            return (
                f"✅ TDS Process Completed Successfully!<br>"
                f"📁 File saved in your Downloads folder:<br>"
                f"- <b>{filename}</b>"
            )

    except Exception as e:
        return f"❌ Error: {e}"
