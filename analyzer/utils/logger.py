"""
analyzer.utils.logger
~~~~~~~~~~~~~~~~~~~~~

Enterprise Multi-Channel Logger for Code Documentation Pipeline:
    1. err_log: Captures runtime errors, unhandled exceptions, and fatal parsing failures.
    2. fn_log: Captures normal operational functioning, timing, and lifecycle events.
    3. quota_complete_log: Specifically logs when API quotas/rate-limits (HTTP 429) are exhausted
       and records the automatic fallback switch to the Grounded Heuristic Engine.
"""

import os
import logging
from datetime import datetime
from typing import Optional


class PipelineLogger:
    """
    Manages three distinct log streams directing output to their respective directories.
    """

    def __init__(self, base_log_dir: str = "logs"):
        self.base_dir = base_log_dir
        self.err_dir = os.path.join(base_log_dir, "err_log")
        self.fn_dir = os.path.join(base_log_dir, "fn_log")
        self.quota_dir = os.path.join(base_log_dir, "quota_complete_log")

        # Ensure all dedicated log directories exist
        os.makedirs(self.err_dir, exist_ok=True)
        os.makedirs(self.fn_dir, exist_ok=True)
        os.makedirs(self.quota_dir, exist_ok=True)

        # Generate timestamped log filenames for the current session
        session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.err_file = os.path.join(self.err_dir, f"error_{session_id}.log")
        self.fn_file = os.path.join(self.fn_dir, f"functioning_{session_id}.log")
        self.quota_file = os.path.join(self.quota_dir, f"quota_switch_{session_id}.log")

        # Configure Loggers
        self.fn_logger = self._setup_logger("pipeline_fn", self.fn_file, logging.INFO)
        self.err_logger = self._setup_logger("pipeline_err", self.err_file, logging.ERROR)
        self.quota_logger = self._setup_logger("pipeline_quota", self.quota_file, logging.WARNING)

    def _setup_logger(self, name: str, log_file: str, level: int) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        # Avoid adding duplicate handlers if already initialized
        if not logger.handlers:
            formatter = logging.Formatter(
                fmt="[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    # 1. Operational Functioning Logs (fn_log)
    def log_fn(self, message: str):
        """Records normal lifecycle operational events."""
        self.fn_logger.info(message)

    # 2. Error Logs (err_log)
    def log_error(self, message: str, exc: Optional[Exception] = None):
        """Records runtime exceptions and failures."""
        if exc:
            self.err_logger.error(f"{message} | Exception: {str(exc)}", exc_info=True)
        else:
            self.err_logger.error(message)

    # 3. Quota Complete / Rate Limit Logs (quota_complete_log)
    def log_quota_exhausted(self, provider: str, model: str, class_name: str, error_details: str):
        """
        Records when API quota is exhausted (429 / resource exhausted)
        and documents the automatic switch to the Heuristic Engine.
        """
        log_entry = (
            f"QUOTA EXHAUSTED for provider '{provider.upper()}' (Model: {model}) while analyzing Class '{class_name}'.\n"
            f"       Reason: {error_details}\n"
            f"       Action Taken: AUTOMATIC FALLBACK SWITCHED TO GROUNDED HEURISTIC ENGINE."
        )
        self.quota_logger.warning(log_entry)

    # 4. Engine Attribution Logs
    def log_engine_used(self, class_name: str, engine_name: str, fallback_reason: Optional[str] = None):
        """
        Records the specific engine (GEMINI, CLAUDE, MISTRAL, or GROUNDED_HEURISTIC)
        used to generate documentation for a given class.
        """
        if fallback_reason:
            msg = f"[ENGINE USED] Class '{class_name}' -> {engine_name} (Fallback Triggered: {fallback_reason})"
        else:
            msg = f"[ENGINE USED] Class '{class_name}' -> {engine_name}"
        self.fn_logger.info(msg)



# Global singleton logger instance
logger = PipelineLogger()
