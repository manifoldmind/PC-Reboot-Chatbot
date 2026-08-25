"""
Контракты данных PCReboot.
"""
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional


@dataclass
class RebootTask:
    """Задача на перезагрузку одного хоста."""
    host: str
    run_id: str
    dry_run: bool = True
    timeout_sec: int = 60
    reboot_delay_sec: int = 5
    method: str = "winrm"
    oarm: bool = False  # Использовать OARM-скрипт


class RebootStatus(str, Enum):
    PENDING = "PENDING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    NOT_ALLOWED = "NOT_ALLOWED"
    PRECHECK_FAILED = "PRECHECK_FAILED"
    AUTH_ERROR = "AUTH_ERROR"
    COMMAND_SENT = "COMMAND_SENT"
    REBOOT_CONFIRMED = "REBOOT_CONFIRMED"
    TIMEOUT = "TIMEOUT"
    COMMAND_ERROR = "COMMAND_ERROR"
    SKIPPED = "SKIPPED"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class RebootResult:
    """Результат обработки одной задачи."""
    host: str
    run_id: str
    status: RebootStatus
    message: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    dry_run: bool = True
    method: str = "winrm"