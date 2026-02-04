import os
from flask import Flask, render_template, request, send_file, after_this_request

# -------------------- IMPORT BUSINESS LOGIC --------------------
from scripts.tds_web import process_tds                 # TDS2
from scripts.tds1_web import process_tds1               # TDS1
from scripts.tds3_web import process_tds3               # TDS3
from scripts.duplicate_finder import process_duplicate  # Duplicate
from scripts.NIS_web import process_nis                 # NIS
from scripts.Retention_web import process_retention     # Retention
from scripts.tds_dynamic import run_tds_rules            # Dynamic TDS
from scripts.gst_logic import process_gst                # GST ITC

# -------------------- APP SETUP --------------------
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------------------- HELPER: AUTO DELETE FILE AFTER DOWNLOAD --------------------
def send_and_cleanup(file_path):
    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        return response

    return send_file(
        file_path,
        as_attachment=True,
        download_name=os.path.basename(file_path),
    )

# -------------------- HOME --------------------
@app.route("/")
def index():
    return render_template("index.html")

# -------------------- TDS 1 --------------------
@app.route("/tds1", methods=["GET", "POST"])
def tds1():
    if request.method == "POST":
        file1 = request.files.get("zfi071")
        file2 = request.files.get("zfitdsrep")

        if not file1 or not file2:
            return render_template("tds1.html", error="⚠️ Please upload both files.")

        file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
        file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
        file1.save(file1_path)
        file2.save(file2_path)

        try:
            output_file = process_tds1(file1_path, file2_path, UPLOAD_FOLDER)
            return send_and_cleanup(output_file)
        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("tds1.html")

# -------------------- TDS 2 --------------------
@app.route("/tds2", methods=["GET", "POST"])
def tds2():
    if request.method == "POST":
        file1 = request.files.get("zfi071")
        file2 = request.files.get("zfitdsrep")

        if not file1 or not file2:
            return render_template("tds2.html", error="⚠️ Please upload both files.")

        file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
        file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
        file1.save(file1_path)
        file2.save(file2_path)

        try:
            output_file = process_tds(file1_path, file2_path, UPLOAD_FOLDER)
            return send_and_cleanup(output_file)
        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("tds2.html")

# -------------------- TDS 3 --------------------
@app.route("/tds3", methods=["GET", "POST"])
def tds3():
    if request.method == "POST":
        file1 = request.files.get("zfi071")
        file2 = request.files.get("zfitdsrep")

        if not file1 or not file2:
            return render_template("tds3.html", error="⚠️ Please upload both files.")

        file1_path = os.path.join(UPLOAD_FOLDER, file1.filename)
        file2_path = os.path.join(UPLOAD_FOLDER, file2.filename)
        file1.save(file1_path)
        file2.save(file2_path)

        try:
            output_file = process_tds3(file1_path, file2_path)
            return send_and_cleanup(output_file)
        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("tds3.html")

# -------------------- DUPLICATE FINDER --------------------
@app.route("/duplicate", methods=["GET", "POST"])
def duplicate():
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return render_template("duplicate.html", error="⚠️ Please upload a file.")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        try:
            output_file = process_duplicate(file_path, UPLOAD_FOLDER)
            return send_and_cleanup(output_file)
        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("duplicate.html")

# -------------------- NIS --------------------
@app.route("/nis", methods=["GET", "POST"])
def nis():
    if request.method == "POST":
        nis_file = request.files.get("nis_file")
        audit_file = request.files.get("audit_file")

        if not nis_file or not audit_file:
            return render_template("NIS.html", error="⚠️ Please upload both files.")

        nis_path = os.path.join(UPLOAD_FOLDER, nis_file.filename)
        audit_path = os.path.join(UPLOAD_FOLDER, audit_file.filename)
        nis_file.save(nis_path)
        audit_file.save(audit_path)

        try:
            output_file = process_nis(nis_path, audit_path)
            return send_and_cleanup(output_file)
        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("NIS.html")

# -------------------- RETENTION --------------------
@app.route("/retention", methods=["GET", "POST"])
def retention():
    if request.method == "POST":
        invoice = request.files.get("invoice")
        vendor = request.files.get("vendor")
        retention_file = request.files.get("retention")

        if not invoice or not vendor or not retention_file:
            return render_template("Retention.html", error="⚠️ Please upload all three files.")

        invoice_path = os.path.join(UPLOAD_FOLDER, invoice.filename)
        vendor_path = os.path.join(UPLOAD_FOLDER, vendor.filename)
        retention_path = os.path.join(UPLOAD_FOLDER, retention_file.filename)

        invoice.save(invoice_path)
        vendor.save(vendor_path)
        retention_file.save(retention_path)

        try:
            output_file = process_retention(invoice_path, vendor_path, retention_path)
            return send_and_cleanup(output_file)
        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("Retention.html")

# -------------------- DYNAMIC TDS --------------------
@app.route("/tds_dynamic", methods=["GET", "POST"])
def tds_dynamic():
    if request.method == "POST":
        file = request.files.get("excel_file")
        rules = request.form.getlist("rules")

        if not file or not rules:
            return render_template(
                "tds_dynamic.html",
                message="⚠️ Please upload file and select at least one rule",
                success=False,
            )

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        try:
            outputs = run_tds_rules(file_path, rules)

            # If multiple files → download first one (or zip later)
            if isinstance(outputs, list) and outputs:
                return send_and_cleanup(outputs[0])

            return render_template(
                "tds_dynamic.html",
                message="⚠️ No output file generated",
                success=False,
            )
        except Exception as e:
            return render_template(
                "tds_dynamic.html",
                message=f"❌ Error: {e}",
                success=False,
            )

    return render_template("tds_dynamic.html")

# -------------------- GST ITC --------------------
@app.route("/gst", methods=["GET", "POST"])
def gst_itc():
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return render_template("gst_itc.html", message="❌ Please upload an Excel file")

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        success, result = process_gst(file_path)

        if success:
            return send_and_cleanup(result)

        return render_template("gst_itc.html", message=f"❌ Error: {result}")

    return render_template("gst_itc.html")

# -------------------- RAILWAY ENTRY POINT --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
