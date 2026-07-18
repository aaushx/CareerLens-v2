import os


class Config:
    """Runtime configuration variables from environment."""

    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_PATH = os.getenv("DATABASE_PATH", "careerlens.db")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", None)

    # Static runtime constraints
    ALLOWED_EXTENSIONS = {"pdf"}
