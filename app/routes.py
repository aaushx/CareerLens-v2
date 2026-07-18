import logging
import os
import re
import threading
import uuid

import fitz
from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session
from werkzeug.utils import secure_filename

from app import database
from app.services.analysis import perform_analysis
from app.services.ocr import extract_text_with_ocr
from app.services.pdf import generate_pdf_report
from app.utils.file_utils import cleanup_old_uploads

logger = logging.getLogger(__name__)

bp = Blueprint("main", __name__)

_warmup_done = False
_warmup_lock = threading.Lock()


def _warmup_imports() -> None:
    """Pre-load sklearn and reportlab in background so analysis requests don't timeout."""
    global _warmup_done
    try:

        logger.info("[WARMUP] Heavy libraries loaded successfully")
    except Exception as e:
        logger.error(f"[WARMUP] Error pre-loading libraries: {e}", exc_info=True)
    _warmup_done = True


# -------------------------------
# Home Route
# -------------------------------
@bp.route("/")
def home():
    global _warmup_done
    with _warmup_lock:
        if not _warmup_done:
            threading.Thread(target=_warmup_imports, daemon=True).start()
    return render_template("index.html")


# -------------------------------
# Upload Temporary Resume Route (AJAX Upload)
# -------------------------------
@bp.route("/upload_temp_resume", methods=["POST"])
def upload_temp_resume():
    # Run cleanup of old files to prevent storage bloat
    cleanup_old_uploads(current_app.config["UPLOAD_FOLDER"])

    if "resume" not in request.files:
        return jsonify({"success": False, "error": "No resume file uploaded"}), 400

    file = request.files["resume"]

    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Only PDF files are allowed"}), 400

    # Extra safety check for file size (5MB)
    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > current_app.config["MAX_CONTENT_LENGTH"]:
            return jsonify({"success": False, "error": "File size exceeds the 5MB limit"}), 413
    except Exception as e:
        logger.error(f"Error validating file size: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Error validating file size: {str(e)}"}), 500

    try:
        base_name = secure_filename(file.filename)
        # Prepend unique prefix
        unique_prefix = str(uuid.uuid4())[:8]
        filename = f"{unique_prefix}_{base_name}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        return jsonify({"success": True, "filename": filename, "original_filename": file.filename})
    except Exception as e:
        logger.error(f"Failed to save temporary file: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"Failed to save temporary file: {str(e)}"}), 500


# -------------------------------
# Upload Route (Renders result.html)
# -------------------------------
@bp.route("/upload", methods=["POST"])
def upload():
    # -------------------------------
    # Validate Request Files / Temp File
    # -------------------------------
    temp_filename = request.form.get("temp_filename", "").strip()
    filename = ""
    filepath = ""

    if temp_filename:
        filename = secure_filename(temp_filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        if not os.path.exists(filepath):
            return (
                render_template(
                    "error.html",
                    error_title="Upload Expired",
                    error_message="The temporary resume file could not be found or has expired. Please try uploading again.",
                    status_code=400,
                    recovery_url="/",
                ),
                400,
            )
    else:
        # Fallback to direct upload
        if "resume" not in request.files:
            return (
                render_template(
                    "error.html",
                    error_title="No File Selected",
                    error_message="No resume file was uploaded. Please go back and select a PDF file.",
                    status_code=400,
                    recovery_url="/",
                ),
                400,
            )

        file = request.files["resume"]

        if file.filename == "":
            return (
                render_template(
                    "error.html",
                    error_title="No Selected File",
                    error_message="No file was selected. Please choose a valid resume in PDF format.",
                    status_code=400,
                    recovery_url="/",
                ),
                400,
            )

        if not file.filename.lower().endswith(".pdf"):
            return (
                render_template(
                    "error.html",
                    error_title="Invalid File Format",
                    error_message="Only resume files in PDF format are allowed. Please convert your resume and try again.",
                    status_code=400,
                    recovery_url="/",
                ),
                400,
            )

        # Enforce size check for fallback direct upload
        try:
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > current_app.config["MAX_CONTENT_LENGTH"]:
                return (
                    render_template(
                        "error.html",
                        error_title="File Too Large",
                        error_message="The uploaded resume file exceeds the maximum size limit of 5MB.",
                        status_code=400,
                        recovery_url="/",
                    ),
                    400,
                )
        except Exception as e:
            logger.error(f"Error validating file size: {e}", exc_info=True)
            return (
                render_template(
                    "error.html",
                    error_title="Size Check Error",
                    error_message="An error occurred while validating the uploaded resume file size.",
                    status_code=500,
                    recovery_url="/",
                ),
                500,
            )

        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

    # -------------------------------
    # Validate Job Description
    # -------------------------------
    if "job_description" not in request.form:
        if temp_filename and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        return (
            render_template(
                "error.html",
                error_title="Job Description Missing",
                error_message="Please enter a target job description to match against your resume.",
                status_code=400,
                recovery_url="/",
            ),
            400,
        )

    job_description = request.form["job_description"]

    if len(job_description.strip()) < 20:
        if temp_filename and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass
        return (
            render_template(
                "error.html",
                error_title="Job Description Too Short",
                error_message="Please enter a target job description of at least 20 characters.",
                status_code=400,
                recovery_url="/",
            ),
            400,
        )

    extracted_text = ""
    extraction_method = "PDF Text Extraction"

    # -------------------------------
    # Text Extraction & Cleanup Wrapper
    # -------------------------------
    try:
        # Normal extraction
        with fitz.open(filepath) as doc:
            for page in doc:
                text = page.get_text()
                if text:
                    extracted_text += text + "\n"

        # OCR Fallback
        if len(extracted_text.strip()) < 100:
            logger.info("PDF text extraction weak. Switching to OCR...")
            extracted_text = extract_text_with_ocr(filepath)
            extraction_method = "OCR Extraction"

    except Exception as e:
        logger.error(f"Error during file extraction: {e}", exc_info=True)
        return (
            render_template(
                "error.html",
                error_title="Text Extraction Failed",
                error_message="An error occurred while reading text from your PDF resume. Please make sure it is not password-protected or corrupted.",
                status_code=500,
                recovery_url="/",
            ),
            500,
        )
    finally:
        # Secure file deletion
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception as e:
                logger.error(f"Error removing temp file {filepath}: {e}")

    # -------------------------------
    # Final Verification
    # -------------------------------
    if len(extracted_text.strip()) == 0:
        return (
            render_template(
                "error.html",
                error_title="No Readable Text",
                error_message="Could not extract any readable text from the uploaded PDF. Please make sure the document contains selectable text or clear print.",
                status_code=400,
                recovery_url="/",
            ),
            400,
        )

    # Clean UUID prefix for DB storage and UI display
    display_filename = filename
    if temp_filename and len(filename) > 9 and filename[8] == "_":
        if re.match(r"^[a-f0-9]{8}$", filename[:8]):
            display_filename = filename[9:]

    results = perform_analysis(extracted_text, job_description, display_filename, extraction_method)

    # Save scan to SQLite database
    try:
        scan_id = database.save_scan(
            session["session_id"], display_filename, extraction_method, job_description, results
        )
        session["last_scan_id"] = scan_id
    except Exception as e:
        logger.error(f"Error saving scan to database: {e}", exc_info=True)

    return render_template("result.html", results_json=results, **results)


# -------------------------------
# Demo Route (POST)
# -------------------------------
@bp.route("/demo", methods=["POST"])
def demo():
    demo_resume_text = """
    Alexander Davis
    Senior React Developer | Full Stack Engineer
    alexander.davis@email.com | +1 (555) 019-2834 | github.com/alexdavis | linkedin.com/in/alexanderdavis

    Summary:
    Dynamic and results-driven Senior React Developer with over 6 years of experience building high-performance web applications. Expert in React, TypeScript, Next.js, and modern state management. Proven track record of optimizing application performance, streamlining CI/CD pipelines, and leading cross-functional teams.

    Technical Skills:
    - Languages: JavaScript (ES6+), TypeScript, HTML5, CSS3, SQL, Python
    - Frameworks & Libraries: React.js, Next.js, Node.js, Express, Tailwind CSS, Bootstrap
    - State Management: Redux Toolkit, Context API, Zustand
    - Database & Tools: PostgreSQL, MongoDB, Redis, Git, Webpack, Vite, Postman
    - DevOps & Cloud: Docker, AWS (S3, EC2), CI/CD (GitHub Actions)

    Professional Experience:
    Senior Front-End Developer | InnovateTech (2022 - Present)
    - Spearheaded the redesign of the core enterprise dashboard using React and TypeScript, boosting load times by 32% and enhancing user engagement.
    - Designed and implemented clean, reusable component libraries with React and Tailwind CSS, reducing development cycle time by 15%.
    - Integrated complex RESTful APIs and established state management patterns using Zustand, improving data consistency across 12+ app views.
    - Mentored 4 junior developers on clean code standards and React hooks best practices.

    Software Engineer | CloudScale Solutions (2020 - 2022)
    - Developed scalable web interfaces in React and Node.js for SaaS clients, serving over 50k active weekly users.
    - Optimized database queries in PostgreSQL, achieving a 20% reduction in API response latency.
    - Built containerized development environments using Docker and automated testing via GitHub Actions.

    Projects:
    Interactive Portfolio & Analytics Tool
    - Built a personal analytics dashboard in Next.js and Tailwind CSS, incorporating interactive Chart.js visualizations.

    Education:
    Bachelor of Science in Computer Science | University of State (2016 - 2020)
    """

    job_description = request.form.get("job_description", "")
    if not job_description or len(job_description.strip()) < 20:
        job_description = """
        Senior React Developer
        Responsibilities:
        - Build responsive, beautiful, and interactive web applications.
        - Translate Figma designs into high-quality code.
        - Master state management, routing, and optimization.
        - Integrate GraphQL APIs and containerize apps.
        Requirements:
        - Expert level React.js, TypeScript, and Tailwind CSS.
        - Hands-on experience with Node.js, GraphQL, and Docker.
        - Familiarity with CI/CD, Git, and cloud services (AWS).
        """

    results = perform_analysis(
        demo_resume_text, job_description, "Alexander_Davis_Lead_Dev.pdf", "Demo Resume Parsing"
    )

    # Save scan to SQLite database
    try:
        scan_id = database.save_scan(
            session["session_id"],
            "Alexander_Davis_Lead_Dev.pdf",
            "Demo Resume Parsing",
            job_description,
            results,
        )
        session["last_scan_id"] = scan_id
    except Exception as e:
        logger.error(f"Error saving scan to database: {e}", exc_info=True)

    return render_template("result.html", results_json=results, **results)


# -------------------------------
# API History Endpoints
# -------------------------------
@bp.route("/api/history", methods=["GET"])
def api_history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify([])
    try:
        scans = database.get_scans(session_id)
        return jsonify(scans)
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        return jsonify([]), 500


@bp.route("/api/history/<int:scan_id>", methods=["GET"])
def api_get_scan(scan_id):
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "No session session_id"}), 400
    try:
        results = database.get_scan(scan_id, session_id)
        if results:
            # Sync session results so PDF generation works for reloaded runs!
            session["last_scan_id"] = scan_id
            return jsonify({"success": True, "results": results})
        return jsonify({"success": False, "error": "Scan not found or unauthorized"}), 404
    except Exception as e:
        logger.error(f"Error fetching scan details: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({"success": False, "error": "No session session_id"}), 400
    try:
        database.clear_scans(session_id)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Error clearing history: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------
# Set Session Results (POST)
# -------------------------------
@bp.route("/set_session_results", methods=["POST"])
def set_session_results():
    data = request.json
    if data:
        try:
            filename = data.get("filename", "unsaved_report.pdf")
            extraction_method = data.get("extraction_method", "API Set Session")
            job_description = data.get("job_description", "N/A")
            scan_id = database.save_scan(
                session["session_id"], filename, extraction_method, job_description, data
            )
            session["last_scan_id"] = scan_id
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error saving session scan: {e}", exc_info=True)
            return jsonify({"success": False, "error": str(e)}), 500
    return jsonify({"success": False, "error": "No data provided"}), 400


# -------------------------------
# Download PDF Route (ReportLab)
# -------------------------------
@bp.route("/download_pdf")
def download_pdf():
    # Read calculations from database using current session's last scan ID
    scan_id = session.get("last_scan_id")
    session_id = session.get("session_id")
    if not scan_id or not session_id:
        return (
            render_template(
                "error.html",
                error_title="Report Not Found",
                error_message="No active report results found to download. Please run a scan first.",
                status_code=400,
                recovery_url="/",
            ),
            400,
        )

    try:
        data = database.get_scan(scan_id, session_id)
        if not data:
            return (
                render_template(
                    "error.html",
                    error_title="Report Not Found",
                    error_message="The requested scan report log could not be retrieved from the database.",
                    status_code=400,
                    recovery_url="/",
                ),
                400,
            )

        pdf_buffer = generate_pdf_report(data)
        return send_file(
            pdf_buffer,
            download_name="ATS_Optimization_Report.pdf",
            as_attachment=True,
            mimetype="application/pdf",
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {e}", exc_info=True)
        return (
            render_template(
                "error.html",
                error_title="PDF Compilation Failed",
                error_message="A server error occurred while compiling your PDF report. Our engineering team has been notified.",
                status_code=500,
                recovery_url="/",
            ),
            500,
        )
