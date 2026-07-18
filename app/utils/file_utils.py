import logging
import os
import time

logger = logging.getLogger(__name__)


def cleanup_old_uploads(upload_folder: str, max_age_seconds: int = 1800) -> None:
    """Deletes temporary files in the uploads folder that are older than the specified limit."""
    try:
        if not os.path.exists(upload_folder):
            return

        now = time.time()
        for filename in os.listdir(upload_folder):
            filepath = os.path.join(upload_folder, filename)
            if os.path.isfile(filepath):
                # Check file age (mtime)
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old temp file: {filename}")
                    except Exception as e:
                        logger.error(f"Error deleting file {filename}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup of old uploads: {e}")
