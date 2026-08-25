"""
Логгер PCReboot.

Принимает RebootResult и дописывает его в JSONL-файл.
Файл создаётся автоматически в папке logs/.
Имя файла: reboot_<run_id>.jsonl
"""

import json
from datetime import datetime
from pathlib import Path

from core.models import RebootResult

def get_week_filename() -> str:
    """
    Возвращает имя файла логов на основе текущей недели.
    Формат: reboot_2026-W34.jsonl
    """
    now = datetime.now()
    year = now.year
    week = now.isocalendar()[1]  # Номер недели (1-53)
    return f"reboot_{year}-W{week:02d}.jsonl"



def result_to_dict(result: RebootResult) -> dict:
    """
    Превращает RebootResult в обычный dict,
    пригодный для json.dumps().
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "host": result.host,
        "run_id": result.run_id,
        "status": result.status.value,
        "message": result.message,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "finished_at": result.finished_at.isoformat() if result.finished_at else None,
        "duration_ms": result.duration_ms,
        "dry_run": result.dry_run,
        "method": result.method,
    }


def log_result(result: RebootResult, log_dir: str = "logs") -> None:
    """
    Дописывает одну строку JSON в файл логов.
    Файл группируется по неделям: logs/reboot_2026-W34.jsonl
    """
    # 1. Создаём папку, если её нет
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 2. Формируем имя файла на основе текущей недели
    file_name = get_week_filename()
    file_path = log_path / file_name

    # 3. Превращаем result в dict, а dict — в JSON-строку
    data = result_to_dict(result)
    json_line = json.dumps(data, ensure_ascii=False)

    # 4. Дописываем строку в файл (режим 'a' = append)
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json_line + "\n")