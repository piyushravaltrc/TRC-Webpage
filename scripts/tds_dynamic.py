import pandas as pd
import os
from datetime import datetime

def run_tds_rules(uploaded_file_path, selected_rules, output_folder):
    """
    Process uploaded Excel file based on selected TDS rules
    and return generated file path for Flask auto-download.

    Parameters:
    uploaded_file_path : str (path of uploaded Excel file)
    selected_rules : list of selected rules
    output_folder : folder where output file will be saved

    Returns:
    str : absolute output file path
    """

    try:
        # Ensure output folder exists (Railway-safe)
        os.makedirs(output_folder, exist_ok=True)

        # -----------------------
        # Step 1: Read Excel file
        # -----------------------
        df = pd.read_excel(uploaded_file_path)

        # -----------------------
        # Step 2: Clean/standardize columns
        # -----------------------
        df["Vendor"] = df["Vendor"].astype(str).str.strip()
        df["Document Number"] = df["Document Number"].astype(str).str.strip()
        df["Total Taxable Value"] = pd.to_numeric(
            df["Total Taxable Value"], errors="coerce"
        ).fillna(0)
        df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")

        # -----------------------
        # Step 3: Apply TDS rules
        # -----------------------
        result_frames = []

        # 194C - Overall ₹1,00,000
        if "194C_OVERALL" in selected_rules:
            df_194C = (
                df[df["TDS Section"] == "194C"]
                .sort_values(["Vendor", "Posting Date"])
                .copy()
            )
            df_194C["Cumulative"] = (
                df_194C.groupby("Vendor")["Total Taxable Value"].cumsum()
            )
            result_frames.append(df_194C[df_194C["Cumulative"] > 100000])

        # 194C - Individual Bill > ₹30,000
        if "194C_INDIVIDUAL" in selected_rules:
            df_194C_ind = df[df["TDS Section"] == "194C"].copy()
            result_frames.append(
                df_194C_ind.groupby("Document Number").filter(
                    lambda x: x["Total Taxable Value"].sum() > 30000
                )
            )

        # 194H - Bill > ₹20,000
        if "194H" in selected_rules:
            df_194H = df[df["TDS Section"] == "194H"].copy()
            result_frames.append(
                df_194H.groupby("Document Number").filter(
                    lambda x: x["Total Taxable Value"].sum() > 20000
                )
            )

        # 194J - Bill > ₹50,000
        if "194J" in selected_rules:
            df_194J = df[df["TDS Section"] == "194J"].copy()
            result_frames.append(
                df_194J.groupby("Document Number").filter(
                    lambda x: x["Total Taxable Value"].sum() > 50000
                )
            )

        # 194Q - Overall ₹50,00,000
        if "194Q" in selected_rules:
            df_194Q = (
                df[df["TDS Section"] == "194Q"]
                .sort_values(["Vendor", "Posting Date"])
                .copy()
            )
            df_194Q["Cumulative"] = (
                df_194Q.groupby("Vendor")["Total Taxable Value"].cumsum()
            )
            result_frames.append(df_194Q[df_194Q["Cumulative"] > 5000000])

        # -----------------------
        # Step 4: Combine results
        # -----------------------
        final_df = (
            pd.concat(result_frames, ignore_index=True)
            if result_frames
            else pd.DataFrame()
        )

        # -----------------------
        # Step 5: Save output file
        # -----------------------
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        output_file = os.path.join(
            output_folder, f"Final_Output_TDS_{timestamp}.xlsx"
        )

        final_df.to_excel(output_file, index=False)

        # ✅ CRITICAL: return FILE PATH (not message)
        return output_file

    except Exception as e:
        raise Exception(str(e))
