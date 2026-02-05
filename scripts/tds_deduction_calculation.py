import pandas as pd
import os
from datetime import datetime


def process_tds_deduction_calculation(uploaded_file_path, selected_rules, output_folder):
    try:
        os.makedirs(output_folder, exist_ok=True)

        df = pd.read_excel(uploaded_file_path)

        df["Vendor"] = df["Vendor"].astype(str).str.strip()
        df["Document Number"] = df["Document Number"].astype(str).str.strip()
        df["Total Taxable Value"] = pd.to_numeric(
            df["Total Taxable Value"], errors="coerce"
        ).fillna(0)
        df["Posting Date"] = pd.to_datetime(df["Posting Date"], errors="coerce")

        result_frames = []

        # 194C - Overall > 1,00,000
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

        # 194C - Individual bill > 30,000
        if "194C_INDIVIDUAL" in selected_rules:
            df_194C = df[df["TDS Section"] == "194C"].copy()
            result_frames.append(
                df_194C.groupby("Document Number").filter(
                    lambda x: x["Total Taxable Value"].sum() > 30000
                )
            )

        # 194H - Bill > 20,000
        if "194H" in selected_rules:
            df_194H = df[df["TDS Section"] == "194H"].copy()
            result_frames.append(
                df_194H.groupby("Document Number").filter(
                    lambda x: x["Total Taxable Value"].sum() > 20000
                )
            )

        # 194J - Bill > 50,000
        if "194J" in selected_rules:
            df_194J = df[df["TDS Section"] == "194J"].copy()
            result_frames.append(
                df_194J.groupby("Document Number").filter(
                    lambda x: x["Total Taxable Value"].sum() > 50000
                )
            )

        # 194Q - Overall > 50,00,000
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

        final_df = (
            pd.concat(result_frames, ignore_index=True)
            if result_frames
            else pd.DataFrame()
        )

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        output_file = os.path.join(
            output_folder, f"Final_Output_TDS_{timestamp}.xlsx"
        )

        final_df.to_excel(output_file, index=False)

        return output_file

    except Exception as e:
        raise Exception(str(e))
