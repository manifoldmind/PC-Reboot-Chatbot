import subprocess
from core.models import RebootTask, RebootResult, RebootStatus
from core.reboot_script_ps import get_oarm_script
from datetime import datetime
import socket


def process_task(task: RebootTask, allowed_hosts: set[str]) -> RebootResult:
    """Принята task = RebootTask -> PROC:process_task()"""
    res = RebootResult(
        host=task.host,
        run_id=task.run_id,
        status=RebootStatus.PENDING,
        message="Задача создана. Ожидание перезагрузки...",
        started_at=datetime.now(),
        dry_run=task.dry_run,
        method=task.method
    )

    # 1. Проверка белого списка
    if task.host not in allowed_hosts:
        res.status = RebootStatus.NOT_ALLOWED
        res.message = f"Host {task.host} isn't in allowed list"
        return res

    # 2. Pre-check порта WinRM (5985)
    if not check_winrm_port(task.host):
        res.status = RebootStatus.PRECHECK_FAILED
        res.message = f"WinRM port 5985 is not accessible on {task.host}"
        return res

    # 3. Dry-run
    if task.dry_run:
        res.status = RebootStatus.SKIPPED
        if task.oarm:
            res.message = "DRY-RUN: OARM script (autosave + reboot)"
        else:
            res.message = f"DRY-RUN: shutdown /r /t {task.reboot_delay_sec} /f"
        return res

    # 4. Реальная отправка команды
    success, msg = send_reboot_command(task.host, task.reboot_delay_sec, task.oarm)

    if success:
        res.status = RebootStatus.COMMAND_SENT
        res.message = msg
    else:
        if "Access Denied" in msg or "Unauthorized" in msg:
            res.status = RebootStatus.AUTH_ERROR
        else:
            res.status = RebootStatus.COMMAND_ERROR
        res.message = msg

    return res


def check_winrm_port(host: str, port: int = 5985, timeout: int = 2) -> bool:
    """Проверяет, открыт ли порт WinRM на целевом хосте."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            return True
    except (socket.timeout, OSError):
        return False


def send_reboot_command(host: str, delay: int, oarm: bool = False) -> tuple[bool, str]:
    """
    Отправляет команду перезагрузки через нативный PowerShell (Invoke-Command).
    Если oarm=True, использует скрипт автосохранения Office.
    """
    try:
        if oarm:
            ps_script = get_oarm_script()
            mode = "OARM (autosave + reboot)"
        else:
            ps_script = f"shutdown /r /f /t {delay}"
            mode = f"shutdown /r /f /t {delay}"

        # Экранируем скрипт для передачи через -Command
        # Используем файл-посредник для надёжности (избегаем проблем с кавычками)
        invoke_command = (
            f'Invoke-Command -ComputerName "{host}" '
            f'-ScriptBlock {{ {ps_script} }}'
        )

        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', invoke_command],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0 and not result.stderr:
            return True, f"Command sent successfully via {mode}"
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown PS error"
            return False, f"PS Error: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Timeout waiting for PowerShell command"
    except Exception as e:
        return False, f"Subprocess Error: {str(e)}"


if __name__ == "__main__":
    print(check_winrm_port("DEAD-PC-999"))
    print(check_winrm_port("localhost"))