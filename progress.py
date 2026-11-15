"""Shared terminal progress reporting."""
import os


def report_progress(percent, message):
    start = float(os.environ.get("FCU_PROGRESS_START", "0"))
    end = float(os.environ.get("FCU_PROGRESS_END", "100"))
    percent = max(0, min(100, percent))
    overall = start + (end - start) * percent / 100
    print(f"[進度 {overall:5.1f}%] {message}", flush=True)
