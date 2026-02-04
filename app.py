from flask import Flask, render_template, request
import os
from scripts.tds_web import process_tds                 # for TDS2
from scripts.tds1_web import process_tds1               # for TDS1
from scripts.tds3_web import process_tds3               # for TDS3    
from scripts.duplicate_finder import process_duplicate  # for Duplicate
from scripts.NIS_web import process_nis                 # for NIS
from scripts.Retention_web import process_retention     # for retention
from scripts.tds_dynamic import run_tds_rules
# from gst_logic import process_gst
from scripts.gst_logic import process_gst
app = Flask(__name__)

# Create upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

# ---------------- TDS 1 ----------------
@app.route('/tds1', methods=['GET', 'POST'])
def tds1():
    if request.method == 'POST':
        file1 = request.files.get('zfi071')
        file2 = request.files.get('zfitdsrep')

        if file1 and file2:
            file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
            file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
            file1.save(file1_path)
            file2.save(file2_path)

            try:
                result_message = process_tds1(file1_path, file2_path, UPLOAD_FOLDER)
                return render_template('result.html', message=result_message, success=True)
            except Exception as e:
                return render_template('result.html', message=f"❌ Error: {e}", success=False)
        else:
            return render_template('tds1.html', error="⚠️ Please upload both files.")
    return render_template('tds1.html')

# ---------------- TDS 2 ----------------
@app.route('/tds2', methods=['GET', 'POST'])
def tds2():
    if request.method == 'POST':
        file1 = request.files.get('zfi071')
        file2 = request.files.get('zfitdsrep')

        if file1 and file2:
            file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
            file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
            file1.save(file1_path)
            file2.save(file2_path)

            try:
                result_message = process_tds(file1_path, file2_path, UPLOAD_FOLDER)
                return render_template('result.html', message=result_message, success=True)
            except Exception as e:
                return render_template('result.html', message=f"❌ Error: {e}", success=False)
        else:
            return render_template('tds2.html', error="⚠️ Please upload both files.")
    return render_template('tds2.html')

# ---------------- TDS 3 ----------------
@app.route('/tds3', methods=['GET', 'POST'])
def tds3():
    if request.method == 'POST':
        file1 = request.files.get('zfi071')
        file2 = request.files.get('zfitdsrep')

        if file1 and file2:
            file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
            file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
            file1.save(file1_path)
            file2.save(file2_path)

            try:
                # process_tds3 returns a message string
                result_message = process_tds3(file1_path, file2_path)
                return render_template('result.html', message=result_message, success=True)

            except Exception as e:
                return render_template('result.html', message=f"❌ Error: {e}", success=False)
        else:
            return render_template('tds3.html', error="⚠️ Please upload both files.")

    return render_template('tds3.html')

# ---------------- DUPLICATE FINDER ----------------
@app.route('/duplicate', methods=['GET', 'POST'])
def duplicate():
    if request.method == 'POST':
        file = request.files.get('file')

        if file and file.filename:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            try:
                result_message = process_duplicate(file_path, UPLOAD_FOLDER)
                return render_template('result.html', message=result_message, success=True)
            except Exception as e:
                return render_template('result.html', message=f"❌ Error: {e}", success=False)
        else:
            return render_template('duplicate.html', error="⚠️ Please upload a file.")
    return render_template('duplicate.html')

# ---------------- NIS ----------------
@app.route('/nis', methods=['GET', 'POST'])
def nis():
    if request.method == 'POST':
        nis_file = request.files.get('nis_file')
        audit_file = request.files.get('audit_file')

        if nis_file and audit_file:
            # Save uploaded files in uploads folder
            nis_path = os.path.join(UPLOAD_FOLDER, nis_file.filename)
            audit_path = os.path.join(UPLOAD_FOLDER, audit_file.filename)
            nis_file.save(nis_path)
            audit_file.save(audit_path)

            try:
                # Run process_nis function (takes 2 arguments)
                result_message = process_nis(nis_path, audit_path)

                # Render success result page
                return render_template('result.html', message=result_message, success=True)
            except Exception as e:
                return render_template('result.html', message=f"❌ Error: {e}", success=False)
        else:
            return render_template('NIS.html', error="⚠️ Please upload both files.")
    return render_template('NIS.html')

# ----------------retention----------------
@app.route('/retention', methods=['GET', 'POST'])
def retention():
    if request.method == 'POST':
        invoice = request.files.get('invoice')
        vendor = request.files.get('vendor')
        retention = request.files.get('retention')

        if invoice and vendor and retention:
            invoice_path = os.path.join(UPLOAD_FOLDER, invoice.filename)
            vendor_path = os.path.join(UPLOAD_FOLDER, vendor.filename)
            retention_path = os.path.join(UPLOAD_FOLDER, retention.filename)

            invoice.save(invoice_path)
            vendor.save(vendor_path)
            retention.save(retention_path)

            try:
                message = process_retention(invoice_path, vendor_path, retention_path)
                return render_template('result.html', message=message, success=True)
            except Exception as e:
                return render_template('result.html', message=f"❌ Error: {e}", success=False)
        else:
            return render_template('Retention.html', error="⚠️ Please upload all three files.")
    return render_template('Retention.html')

@app.route("/tds_dynamic", methods=["GET", "POST"])
def tds_dynamic():
    if request.method == "POST":
        file = request.files.get("excel_file")
        rules = request.form.getlist("rules")

        if not file or not rules:
            return render_template(
                "tds_dynamic.html",
                message="⚠️ Please upload file and select at least one rule",
                success=False
            )

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        try:
            outputs = run_tds_rules(file_path, rules)
            return render_template(
                "tds_dynamic.html",
                message=f"✅ Generated files in Downloads: {', '.join(outputs)}",
                success=True
            )
        except Exception as e:
            return render_template(
                "tds_dynamic.html",
                message=f"❌ Error: {e}",
                success=False
            )

    return render_template("tds_dynamic.html")

@app.route("/", methods=["GET", "POST"])
def gst_itc():
    message = ""

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            message = "❌ Please upload an Excel file"
        else:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)

            success, result = process_gst(file_path)

            if success:
                message = (
                    "✅ GST ITC Analysis Completed Successfully!<br>"
                    "📁 File saved in Downloads:<br>"
                    f"<b>{result}</b>"
                )
            else:
                message = f"❌ Error: {result}"

    return render_template("gst_itc.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
