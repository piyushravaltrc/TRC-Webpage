import pandas as pd
import os
from datetime import datetime
import re


def process_tds3(zfi_file, zfit_file, output_folder):
    try:
        os.makedirs(output_folder, exist_ok=True)

        zfi_df = pd.read_excel(zfi_file)
        zfit_df = pd.read_excel(zfit_file)

        for df in (zfi_df, zfit_df):
            df["Company Code"] = (
                df["Company Code"].astype(str).str.replace(".0", "", regex=False).str.strip()
            )
            df["Vendor"] = (
                df["Vendor"]
                .astype(str)
                .str.replace(".0", "", regex=False)
                .str.strip()
                .str.lstrip("0")
            )
            df["Document No."] = (
                df["Document No."].astype(str).str.replace(".0", "", regex=False).str.strip()
            )

        zfi_df["Unique_Key"] = (
            zfi_df["Company Code"] + "-" +
            zfi_df["Vendor"] + "-" +
            zfi_df["Document No."]
        )

        zfit_df["Unique_Key"] = (
            zfit_df["Company Code"] + "-" +
            zfit_df["Vendor"] + "-" +
            zfit_df["Document No."]
        )

        po_mapping = zfi_df[["Unique_Key", "PO No.", "Item Text"]].drop_duplicates()

        merged_df = pd.merge(
            zfit_df,
            po_mapping,
            on="Unique_Key",
            how="left"
        )

        filtered_df = merged_df[
            merged_df["PO No._x"].notna()
            & (merged_df["PO No._x"].astype(str).str.strip() != "")
        ]

        filtered_df = filtered_df[
            ~filtered_df["Ref. Docnr."].astype(str).str.contains(
                "rev", case=False, na=False
            )
        ]

        po_value_groups = (
            filtered_df.groupby(["PO No._x", "Base Value"])
            .size()
            .reset_index(name="count")
        )

        po_value_pivot = po_value_groups.pivot_table(
            index="PO No._x",
            columns="Base Value",
            values="count",
            fill_value=0,
        )

        po_no_to_remove = []
        for po_no, values in po_value_pivot.iterrows():
            for value in values.index:
                if value > 0 and -value in values.index:
                    if values[value] > 0 and values[-value] > 0:
                        po_no_to_remove.append(po_no)
                        break

        filtered_df = filtered_df[
            ~filtered_df["PO No._x"].isin(po_no_to_remove)
        ]

        tds_sections = filtered_df.groupby("PO No._x")["TDS Section"].agg(set)
        po_no_to_exclude = [
            po for po, sections in tds_sections.items()
            if {"194Q", "194C"}.issubset(sections)
        ]

        filtered_df = filtered_df[
            ~filtered_df["PO No._x"].isin(po_no_to_exclude)
        ]

        keywords = [
            "prof", "professional", "consultancy", "auditing", "audit", "legal",
            "medical", "engineering", "architecture", "architect", "interior",
            "interior designer", "decoration", "accounting", "accountancy",
            "book keeping", "advertising",
        ]

        filtered_df["Item Text"] = filtered_df["Item Text"].astype(str).str.lower()
        mask_keyword = filtered_df["Item Text"].apply(
            lambda x: any(k in x for k in keywords)
        )
        mask_tds = filtered_df["TDS Rate"].fillna(0) < 10

        filtered_df = filtered_df[mask_keyword & mask_tds]

        cn_keywords = ["CN", "DN", "CREDIT NOTE", "DEBIT NOTE"]
        pattern = r"\b(?:{})\b".format("|".join(map(re.escape, cn_keywords)))

        filtered_df = filtered_df[
            ~filtered_df["Item Text"].str.contains(pattern, case=False, na=False)
        ]

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        output_file = os.path.join(
            output_folder,
            f"Final_Output_TDS3_{timestamp}.xlsx"
        )

        filtered_df.to_excel(output_file, index=False)

        return output_file

    except Exception as e:
        raise Exception(str(e))
