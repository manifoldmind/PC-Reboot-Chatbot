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
    
    # 0. Валидация (на всякий случай)
    if not task.host or not task.host.strip():
        res.status = RebootStatus.VALIDATION_FAILED
        res.message = "Пустое имя хоста"
        return res

    # #ARCHV 1. Проверка белого списка
    # if task.host not in allowed_hosts:
    #     res.status = RebootStatus.NOT_ALLOWED
    #     res.message = f"Host {task.host} isn't in allowed list"
    #     return res

    # 1. ПРОВЕРКА БЕЛОГО СПИСКА (Приоритет №1)
    # Если хоста нет в списке, мы его даже не пытаемся пинговать (безопасность + скорость)
    if task.host not in allowed_hosts:
        res.status = RebootStatus.NOT_ALLOWED
        res.message = f"Host {task.host} isn't in allowed list"
        return res
    
    # 2. ДИАГНОСТИКА СЕТИ (Приоритет №2)
    # Если хост в списке, но недоступен — пишем детальную причину  
    is_ok, reason = diagnose_host(task.host)
    if not is_ok:
        res.status = RebootStatus.PRECHECK_FAILED
        res.message = reason
        return res
    
    #ARCHV:
    # # 2. Pre-check порта WinRM (5985)
    # if not check_winrm_port(task.host):
    #     res.status = RebootStatus.PRECHECK_FAILED
    #     res.message = f"WinRM port 5985 is not accessible on {task.host}"
    #     return res

    # 3. DRY-RUN (Приоритет №3)
    # Если все проверки пройдены, но режим тестовый — останавливаемся
    if task.dry_run:
        res.status = RebootStatus.SKIPPED
        if task.oarm:
            res.message = "DRY-RUN: OARM script (autosave + reboot)"
        else:
            res.message = f"DRY-RUN: shutdown /r /t {task.reboot_delay_sec} /f"
        return res

    # 4. РЕАЛЬНОЕ ВЫПОЛНЕНИЕ
    success, msg = send_reboot_command(task.host, task.reboot_delay_sec, task.oarm)

    if success:
        res.status = RebootStatus.COMMAND_SENT
        res.message = msg
    else:
        if "Access Denied" in msg or "Unauthorized" in msg or "404" in msg:
            res.status = RebootStatus.AUTH_ERROR
        else:
            res.status = RebootStatus.COMMAND_ERROR
        res.message = msg

    return res

def diagnose_host(host: str) -> tuple[bool, str]:
    """
    Проверяет доступность хоста по слоям.
    Возвращает (Успех, Причина_ошибки).
    """
    # Слой 1: DNS Resolution
    try: 
        # Пытаемся получить IP по имени. Если имя кривое — упадет здесь
        socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False, f"DNS resolution failed (Host '{host}' not found)"
    
    # Слой 2: Ping (ICMP)
    # Используем subprocess, так как это надежнее всего в Windows
    try:
        # -n (один пакет), -w 1000 (таймаут 1 сек)
        result = subprocess.run(
            ['ping', '-n', '1', '-w', '1000', host],
            capture_output=True,
            text=True,
            timeout=5
        )
        # В русском Windows успех это "Ответ от", в английском "Reply from"
        # Но надежнее смотреть код возврата или наличие "TTL="
        if "TTL=" not in result.stdout and "TTL=" not in result.stdout.upper():
            # Иногда ping возвращает 0, но пишет "Превышен интервал ожидания"
            if "Превышен" in result.stdout or "timed out" in result.stdout.lower():
                return False, f"Ping failed (Host unreachable)"
    
    except Exception:
        pass # Игнорируем ошибки самого пинга, идем дальше к порту

    # Слой 3: Port Check (WinRM 5985)
    try:
        # Проверяем качество самой трубы - сессии порта 5985
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect((host, 5985))
            return True, "OK" # Если дошли сюда — всё отлично
    except (socket.timeout, OSError):
        return False, f"Port 5985 closed (WinRM not accessible)"
    
    return False, "Unknown network error"
    
# ARCHV:
# def check_winrm_port(host: str, port: int = 5985, timeout: int = 2) -> bool:
#     """Проверяет, открыт ли порт WinRM на целевом хосте."""
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#             sock.settimeout(timeout)
#             sock.connect((host, port))
#             return True
#     except (socket.timeout, OSError):
#         return False


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
    print(f"Пречек локалхоста {diagnose_host("localhost")}")
    print(f"Пречек фейка: {diagnose_host("DEAD-PC-999")}")
    print(f"Пречек oarm-1224: {diagnose_host("oarm-1224.nsd.ru")}")