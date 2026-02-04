import pandas as pd
import re
import os
from datetime import datetime

# def process_nis(nis_path, audit_path):
def process_nis(nis_path, audit_path, output_folder):
    try:
        # Step 1: Load Excel files
        nis_dump = pd.read_excel(nis_path)
        audit_universe = pd.read_excel(audit_path)

        # Step 2: Clean column names
        nis_dump.columns = nis_dump.columns.str.strip()

        # Step 3: Remove blank 'Status' rows
        if 'Status' in nis_dump.columns:
            nis_dump = nis_dump[nis_dump['Status'].notna() & (nis_dump['Status'] != '')]
        elif 'Status of checklist' in nis_dump.columns:
            nis_dump = nis_dump[nis_dump['Status of checklist'].notna() & (nis_dump['Status of checklist'] != '')]
        else:
            return "❌ Neither 'Status' nor 'Status of checklist' column found in NIS file."

        # Step 4: Remove specific vendor names
        if 'Vendor / Employee Name' in nis_dump.columns:
            keywords = ['Adani', 'Ambuja', 'ACC Ltd', 'Belvedere']
            pattern = '|'.join(keywords)
            nis_dump = nis_dump[~nis_dump['Vendor / Employee Name'].str.contains(pattern, case=False, na=False)]

        # Step 5: Define expense-related keywords
        expense_keywords_5000 = ['Courier', 'printing', 'Medicine', 'Fire & Safety', 'Housekeeping', 
                                 'Pest Control', 'Horticulture', 'stationary', 'stationery', 'Courior']
        expense_keywords_10000 = ['Vehicle Hiring', 'Fuel', 'Cab', 'Petrol', 'Diesel']
        expense_keywords_20000 = ['Repair', 'Equipment', 'Food', 'Beverages', 'Travel', 
                                  'Business Promotion', 'Staff Welfare', 'Maintenance', 'Travelling']

        expense_pattern_5000 = r'\b(' + r'|'.join(expense_keywords_5000) + r')\b'
        expense_pattern_10000 = r'\b(' + r'|'.join(expense_keywords_10000) + r')\b'
        expense_pattern_20000 = r'\b(' + r'|'.join(expense_keywords_20000) + r')\b'

        specific_keywords = [
            'Land purchase', 'Land Development', 'legal charges', 'Brokerage', 'Commission', 
            'Consultancy', 'Professional', 'Rating', 'TRA', 'Underwriting', 'court', 
            'Rental charges', 'Society Maintaintence', 'Training expenses', 'Talent development', 
            'Assessment', 'Seminar', 'Conference', 'Filing', 'Listing fees', 'CSR', 'Bid', 
            'Tender', 'Land', 'legal', 'Prof', 'Consul', 'Audit', 'Rental'
        ]
        specific_keywords_pattern = r'\b(' + r'|'.join(specific_keywords) + r')\b'

        def find_keyword_based_exceptions_by_amount(df, amount_threshold, expense_pattern):
            return df[df['Purpose of Expense'].str.contains(expense_pattern, case=False, na=False) & 
                    (df['Total Invoice Amount'] > amount_threshold)]

        def find_specific_keyword_rows(df, keyword_pattern):
            return df[df['Purpose of Expense'].str.contains(keyword_pattern, case=False, na=False)]

        # Step 6: Find exceptions
        expense_5000_df = find_keyword_based_exceptions_by_amount(nis_dump, 5000, expense_pattern_5000)
        expense_10000_df = find_keyword_based_exceptions_by_amount(nis_dump, 10000, expense_pattern_10000)
        expense_20000_df = find_keyword_based_exceptions_by_amount(nis_dump, 20000, expense_pattern_20000)
        specific_5000_df = find_keyword_based_exceptions_by_amount(nis_dump, 5000, specific_keywords_pattern)
        specific_10000_df = find_keyword_based_exceptions_by_amount(nis_dump, 10000, specific_keywords_pattern)
        specific_20000_df = find_keyword_based_exceptions_by_amount(nis_dump, 20000, specific_keywords_pattern)
        specific_keywords_rows_df = find_specific_keyword_rows(nis_dump, specific_keywords_pattern)

        # Step 7: Remove vendors that match company names in Audit Universe
        nis_dump = nis_dump[~nis_dump['Vendor / Employee Name'].isin(audit_universe['Name of Company'])]

        # Step 8: Save outputs to Downloads with timestamp
        os.makedirs(output_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        output_path = os.path.join(output_folder, f"NIS_Splitting_{timestamp}.xlsx")


        with pd.ExcelWriter(output_path) as writer:
            expense_5000_df.to_excel(writer, sheet_name='Exceptions <= 5000', index=False)
            expense_10000_df.to_excel(writer, sheet_name='Exceptions <= 10000', index=False)
            expense_20000_df.to_excel(writer, sheet_name='Exceptions <= 20000', index=False)
            specific_5000_df.to_excel(writer, sheet_name='Specific Keyword <= 5000', index=False)
            specific_10000_df.to_excel(writer, sheet_name='Specific Keyword <= 10000', index=False)
            specific_20000_df.to_excel(writer, sheet_name='Specific Keyword <= 20000', index=False)
            specific_keywords_rows_df.to_excel(writer, sheet_name='All Specific Keyword Rows', index=False)

        # return f"✅ Processing complete! File saved to Downloads folder:\n{output_path}"
        return output_path
    
    except Exception as e:
        # return f"❌ Error: {str(e)}"
        raise Exception(str(e))
