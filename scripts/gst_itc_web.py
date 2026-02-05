import pandas as pd
import os
from datetime import datetime

# ==============================
# LOG FUNCTION
# ==============================
def write_log(message):
    log_file = "GST_ITC_Log.txt"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M:%S} | {message}\n")


# ==============================
# GST CONFIG
# ==============================
KEYWORDS = [
    "car", "colony housekeeping", "worker bus", "vehicle hire", "local round",
    "mercedes", "cater", "staff bus", "royal hotel", "hotel exp", "f&b",
    "tours", "travels", "innova", "eco van", "colony borewell",
    "worker colony", "food waste", "food collection of colony",
    "local trip charge", "hotel booking", "worker pickup-drop",
    "vehicle trip", "travel exp", "uniform"
]

EXCLUDE_PO = ["petrol", "diesel", "cng gas"]
EXCLUDE_VENDOR = [
    "torrent power", "uttar gujarat vij", "ugvcl",
    "fp eco energy", "nandan terry", "municipal commissioner"
]


# ==============================
# MAIN GST FUNCTION
# ==============================
def process_gst_itc(file_path, output_folder):
    try:
        if not file_path.endswith((".xlsx", ".xls")):
            raise Exception("Invalid file format. Please upload Excel file")

        df = pd.read_excel(file_path)

        if df.empty:
            raise Exception("Uploaded file is empty")

        required_cols = [
            "PO Short Text",
            "Vendor Name",
            "Tax Code _I",
            "Tax Code _P"
        ]

        for col in required_cols:
            if col not in df.columns:
                raise Exception(f"Missing required column: {col}")

        df["PO_TEXT_LC"] = df["PO Short Text"].astype(str).str.lower()
        df["VENDOR_LC"] = df["Vendor Name"].astype(str).str.lower()

        def keyword_match(text):
            return any(k in text for k in KEYWORDS)

        def exclude_match(po_text, vendor_text):
            return (
                any(k in po_text for k in EXCLUDE_PO)
                or any(k in vendor_text for k in EXCLUDE_VENDOR)
            )

        df["KEYWORD_MATCH"] = df["PO_TEXT_LC"].apply(keyword_match)
        df["EXCLUDE_MATCH"] = df.apply(
            lambda x: exclude_match(x["PO_TEXT_LC"], x["VENDOR_LC"]),
            axis=1
        )

        ineligible = []
        eligible_not_taken = []
        others = []
        deviation = []
        excluded = []

        for _, row in df.iterrows():
            if row["EXCLUDE_MATCH"]:
                excluded.append(row)
                continue

            po_match = row["KEYWORD_MATCH"]
            tax_i = str(row["Tax Code _I"]).strip()
            tax_p = str(row["Tax Code _P"]).strip()

            if tax_i != tax_p:
                deviation.append(row)
            elif po_match and tax_i == "&A":
                ineligible.append(row)
            elif (not po_match) and tax_i == "&E":
                eligible_not_taken.append(row)
            else:
                others.append(row)

        os.makedirs(output_folder, exist_ok=True)

        output_file = os.path.join(
            output_folder,
            f"GST_ITC_Output_{datetime.now():%d-%m-%Y_%H-%M}.xlsx"
        )

        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            pd.DataFrame(ineligible).to_excel(writer, "Ineligible ITC Taken", index=False)
            pd.DataFrame(eligible_not_taken).to_excel(writer, "Eligible ITC Not Taken", index=False)
            pd.DataFrame(others).to_excel(writer, "Others", index=False)
            pd.DataFrame(deviation).to_excel(writer, "Deviation", index=False)
            pd.DataFrame(excluded).to_excel(writer, "Excluded", index=False)

        write_log(f"GST ITC processed successfully: {output_file}")

        return output_file

    except Exception as e:
        write_log(f"GST ITC Error: {e}")
        raise Exception(str(e))
