import logging
import os
import sys
import uuid

from flask import Flask, session


def create_app() -> Flask:
    """Application Factory. Creates, configures, and returns a Flask app instance."""

    # 1. Centralized logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d]: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger = logging.getLogger(__name__)

    # 2. Production SECRET_KEY validation
    flask_env = os.getenv("FLASK_ENV", "production")
    secret_key = os.getenv("SECRET_KEY")

    if flask_env == "production":
        if not secret_key:
            logger.critical("SECRET_KEY environment variable is missing in production!")
            sys.exit("Critical Error: SECRET_KEY is not set in production mode.")
        elif secret_key == "ats-secret-key-optimization-platform-2026":
            logger.critical("Insecure default SECRET_KEY is being used in production!")
            sys.exit("Critical Error: Default SECRET_KEY is not allowed in production mode.")
    else:
        # Development fallback
        secret_key = secret_key or "ats-development-key-fallback-2026"

    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = secret_key

    # 3. Load configurations
    from app.config import Config

    app.config.from_object(Config)
    app.config["SECRET_KEY"] = secret_key
    app.secret_key = secret_key

    # Ensure the upload folder exists
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        try:
            os.makedirs(app.config["UPLOAD_FOLDER"])
        except Exception as e:
            logger.error(f"Failed to create UPLOAD_FOLDER: {e}", exc_info=True)

    # Configure pytesseract command path if specified
    tesseract_cmd = app.config["TESSERACT_CMD"]
    if tesseract_cmd and os.path.exists(tesseract_cmd):
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        logger.info(f"Tesseract path successfully overridden: {tesseract_cmd}")

    # 4. Session management hooks
    @app.before_request
    def ensure_session_id():
        if "session_id" not in session:
            session["session_id"] = str(uuid.uuid4())

    # 5. Payload size constraint and unhandled errors handling
    @app.errorhandler(404)
    def page_not_found(error):
        from flask import render_template

        return (
            render_template(
                "error.html",
                error_title="Page Not Found",
                error_message="The page you are looking for does not exist or has been moved.",
                status_code=404,
                recovery_url="/",
            ),
            404,
        )

    @app.errorhandler(413)
    def request_entity_too_large(error):
        from flask import jsonify, render_template, request

        if (
            request.path.startswith("/api/")
            or request.headers.get("Content-Type") == "application/json"
            or request.path == "/upload_temp_resume"
        ):
            return (
                jsonify({"success": False, "error": "File size exceeds the maximum limit of 5MB"}),
                413,
            )
        return (
            render_template(
                "error.html",
                error_title="File Too Large",
                error_message="The uploaded resume file exceeds the maximum size limit of 5MB.",
                status_code=413,
                recovery_url="/",
            ),
            413,
        )

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        logger.error(f"Unhandled Internal Server Error: {error}", exc_info=True)
        from flask import jsonify, render_template, request

        if (
            request.path.startswith("/api/")
            or request.headers.get("Content-Type") == "application/json"
        ):
            return jsonify({"success": False, "error": "An internal server error occurred."}), 500
        return (
            render_template(
                "error.html",
                error_title="Internal Server Error",
                error_message="An unexpected server error occurred while processing your request. Our engineering team has been notified.",
                status_code=500,
                recovery_url="/",
            ),
            500,
        )

    # 6. Database Initialization
    from app import database

    try:
        database.init_db(app.config["DATABASE_PATH"])
        logger.info(f"SQLite database initialized successfully at: {app.config['DATABASE_PATH']}")
    except Exception as e:
        logger.critical(f"Failed to initialize SQLite database: {e}", exc_info=True)

    # 7. Blueprints Registration
    from app.routes import bp

    app.register_blueprint(bp)

    return app
