""" Список статусов операции:
PENDING
VALIDATION_FAILED
NOT_ALLOWED
PRECHECK_FAILED
AUTH_ERROR
COMMAND_SENT
REBOOT_CONFIRMED
TIMEOUT
COMMAND_ERROR
SKIPPED
UNKNOWN_ERROR
"""

"""
Контракты данных PCReboot.

Файл описывает структуры данных, которые используются всеми слоями системы:
- CLI создаёт RebootTask;
- core обрабатывает задачу и возвращает RebootResult;
- логи/отчёты используют RebootResult;
- будущие интеграции Naumen/BotX также смогут использовать эти структуры.

Файл НЕ выполняет сетевых операций и НЕ печатает пользователю.
"""
"""DATA: -> ok
host = WS-K534D
run_id = run-0001
status = REBOOT_CONFIRMED
message = ...
started_at = ...
finished_at = ...
duration_ms = ...
dry_run = ...
method = ...
"""
from dataclasses import dataclass

@dataclass
class RebootTask:
    """
    Задача на перезагрузку одного хоста.

    Это входной объект для core.
    CLI или будущий бот создаёт такой объект и передаёт в ядро.
    """
    
    host: str #хост ЦПК
    run_id: str #название сессии
    dry_run: bool = True #безопасный ли режим 
    timeout_sec: int = 60 #таймаут операции
    reboot_delay_sec: int = 5 #	задержка для shutdown /r /t 5
    method: str = "winrm" #транспорт: winrm

from enum import Enum 

class RebootStatus(str, Enum):
    """
    Допустимые статусы обработки одной задачи перезагрузки.
    """

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
    
    
from datetime import datetime
from typing import Optional 

@dataclass
class RebootResult:
    """
    Результат обработки одной задачи перезагрузки.

    Этот объект будет возвращаться ядром.
    CLI будет показывать его пользователю.
    Логгер будет писать его в JSONL.
    """
    
    host: str
    run_id: str
    status: RebootStatus
    message: str #перезагр/нет
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    dry_run: bool = True
    method: str = "winrm"  
    
