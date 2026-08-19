from .models import RebootTask, RebootResult, RebootStatus
from datetime import datetime
import socket

#CONFIRMED:DONE
def process_task(task: RebootTask, allowed_hosts: set[str]) -> RebootResult: #WARN: task ТОЛЬКО ДЛЯ ВХОДНЫХ ЗАДАЧ от юзера, не состояние выполнения задачи
    """
    Принята task = RebootTask -> PROC:process_task()
    """
    # Пока только:
    # - проверка allowed_hosts;
    # - dry-run;
    # - без реального WinRM.

    res = RebootResult(
        host=task.host,
        run_id=task.run_id,
        status=RebootStatus.PENDING,
        message="Задача создана. Ожидание перезагрузки...",
        started_at=datetime.now(),
        dry_run=task.dry_run,
        method=task.method
    )
    
    # MADE: если task.host нет в allowed_hosts, вернуть NOT_ALLOWED
    if task.host not in allowed_hosts:
        res.status=RebootStatus.NOT_ALLOWED
        res.message = f"Host {task.host} isn't in allowed list"
        return res

    # Pre-check порта WinRM
    if not check_winrm_port(task.host):
        res.status = RebootStatus.PRECHECK_FAILED
        res.message = f"WinRM port 5985 is not accessible on {task.host}"
        return res
    # MADE: если task.dry_run, вернуть SKIPPED
    # MADE: message должен показывать команду, которая была бы выполнена:
    # shutdown /r /t {task.reboot_delay_sec} /f
    if task.dry_run:
        res.status=RebootStatus.SKIPPED
        res.message=f"DRY-RUN: shutdown /r /t {task.reboot_delay_sec} /f"
        return res
        

    # MADE: если не dry-run, пока вернуть COMMAND_ERROR
    # message: "Real backend not implemented yet"    
    #STUB:
    res.status=RebootStatus.COMMAND_ERROR
    res.message="Real backend not implemented yet"
    return res

def check_winrm_port(host: str, port: int = 5985, timeout: int = 2) -> bool:
    """
    Проверяет, открыт ли порт WinRM на целевом хосте.
    Возвращает True, если порт открыт, иначе False.
    """
    # TODO: 
    # 1. Создать сокет: socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 2. Установить таймаут: sock.settimeout(timeout)
    # 3. Попытаться подключиться: sock.connect((host, port))
    # 4. Если получилось — закрыть сокет (sock.close()) и вернуть True
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((host, port))
            return True
    # 5. Если упало с ошибкой (socket.timeout, OSError) — вернуть False
    except (socket.timeout, OSError):
        return False


# # Тест с заведомо недоступным хостом
# print(check_winrm_port("DEAD-PC-999"))  # Ожидаемо: False

# # Тест с localhost (если WinRM не запущен локально)
# print(check_winrm_port("localhost"))    # Ожидаемо: False

# # Тест с реальным хостом (если есть)
# print(check_winrm_port("WS-K534D"))     # Зависит от среды

if __name__ == "__main__":
    # Тест с заведомо недоступным хостом
    print(check_winrm_port("DEAD-PC-999"))  
    print(check_winrm_port("localhost"))    
    print(check_winrm_port("WS-K534D"))     