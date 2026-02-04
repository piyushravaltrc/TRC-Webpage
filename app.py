import os
from flask import (
    Flask,
    render_template,
    request,
    send_file,
    after_this_request,
)

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

# -------------------- HELPERS --------------------
def is_file_path(value):
    return isinstance(value, str) and os.path.exists(value)

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
        f1 = request.files.get("zfi071")
        f2 = request.files.get("zfitdsrep")

        if not f1 or not f2:
            return render_template("tds1.html", error="⚠️ Please upload both files.")

        p1 = os.path.join(UPLOAD_FOLDER, f1.filename)
        p2 = os.path.join(UPLOAD_FOLDER, f2.filename)
        f1.save(p1)
        f2.save(p2)

        try:
            result = process_tds1(p1, p2, UPLOAD_FOLDER)

            if is_file_path(result):
                return send_and_cleanup(result)

            return render_template("result.html", message=result, success=True)

        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("tds1.html")

# -------------------- TDS 2 --------------------
@app.route("/tds2", methods=["GET", "POST"])
def tds2():
    if request.method == "POST":
        f1 = request.files.get("zfi071")
        f2 = request.files.get("zfitdsrep")

        if not f1 or not f2:
            return render_template("tds2.html", error="⚠️ Please upload both files.")

        p1 = os.path.join(UPLOAD_FOLDER, f1.filename)
        p2 = os.path.join(UPLOAD_FOLDER, f2.filename)
        f1.save(p1)
        f2.save(p2)

        try:
            result = process_tds(p1, p2, UPLOAD_FOLDER)

            if is_file_path(result):
                return send_and_cleanup(result)

            return render_template("result.html", message=result, success=True)

        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("tds2.html")

# -------------------- TDS 3 --------------------
@app.route("/tds3", methods=["GET", "POST"])
def tds3():
    if request.method == "POST":
        f1 = request.files.get("zfi071")
        f2 = request.files.get("zfitdsrep")

        if not f1 or not f2:
            return render_template("tds3.html", error="⚠️ Please upload both files.")

        p1 = os.path.join(UPLOAD_FOLDER, f1.filename)
        p2 = os.path.join(UPLOAD_FOLDER, f2.filename)
        f1.save(p1)
        f2.save(p2)

        try:
            result = process_tds3(p1, p2)

            if is_file_path(result):
                return send_and_cleanup(result)

            return render_template("result.html", message=result, success=True)

        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("tds3.html")

# -------------------- DUPLICATE --------------------
@app.route("/duplicate", methods=["GET", "POST"])
def duplicate():
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return render_template("duplicate.html", error="⚠️ Please upload a file.")

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        try:
            result = process_duplicate(path, UPLOAD_FOLDER)

            if is_file_path(result):
                return send_and_cleanup(result)

            return render_template("result.html", message=result, success=True)

        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("duplicate.html")

# -------------------- NIS --------------------
@app.route("/nis", methods=["GET", "POST"])
def nis():
    if request.method == "POST":
        nfile = request.files.get("nis_file")
        afile = request.files.get("audit_file")

        if not nfile or not afile:
            return render_template("NIS.html", error="⚠️ Please upload both files.")

        np = os.path.join(UPLOAD_FOLDER, nfile.filename)
        ap = os.path.join(UPLOAD_FOLDER, afile.filename)
        nfile.save(np)
        afile.save(ap)

        try:
            result = process_nis(np, ap)

            if is_file_path(result):
                return send_and_cleanup(result)

            return render_template("result.html", message=result, success=True)

        except Exception as e:
            return render_template("result.html", message=f"❌ Error: {e}", success=False)

    return render_template("NIS.html")

# -------------------- RETENTION --------------------
@app.route("/retention", methods=["GET", "POST"])
def retention():
    if request.method == "POST":
        inv = request.files.get("invoice")
        ven = request.files.get("vendor")
        ret = request.files.get("retention")

        if not inv or not ven or not ret:
            return render_template("Retention.html", error="⚠️ Please upload all three files.")

        ip = os.path.join(UPLOAD_FOLDER, inv.filename)
        vp = os.path.join(UPLOAD_FOLDER, ven.filename)
        rp = os.path.join(UPLOAD_FOLDER, ret.filename)
        inv.save(ip)
        ven.save(vp)
        ret.save(rp)

        try:
            result = process_retention(ip, vp, rp)

            if is_file_path(result):
                return send_and_cleanup(result)

            return render_template("result.html", message=result, success=True)

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

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        try:
            outputs = run_tds_rules(path, rules)

            if isinstance(outputs, list) and outputs and is_file_path(outputs[0]):
                return send_and_cleanup(outputs[0])

            return render_template(
                "tds_dynamic.html",
                message="✅ Process completed successfully",
                success=True,
            )

        except Exception as e:
            return render_template(
                "tds_dynamic.html",
                message=f"❌ Error: {e}",
                success=False,
            )

    return render_template("tds_dynamic.html")

# -------------------- GST --------------------
@app.route("/gst", methods=["GET", "POST"])
def gst_itc():
    if request.method == "POST":
        file = request.files.get("file")

        if not file:
            return render_template("gst_itc.html", message="❌ Please upload an Excel file")

        path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(path)

        success, result = process_gst(path)

        if success and is_file_path(result):
            return send_and_cleanup(result)

        return render_template("gst_itc.html", message=result)

    return render_template("gst_itc.html")

# -------------------- ENTRY POINT --------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
