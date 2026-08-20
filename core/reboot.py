from .models import RebootTask, RebootResult, RebootStatus
from datetime import datetime
import socket
import winrm

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
    #HOLD:
    # res.status=RebootStatus.COMMAND_ERROR
    # res.message="Real backend not implemented yet"
    # return res
    
    # Реальная отправка команды
    success, msg = send_reboot_command(task.host, task.reboot_delay_sec)
    
    if success:
        res.status = RebootStatus.COMMAND_SENT
        res.message = msg
    
    else:
        # Если ошибка авторизации - ставим AUTH_ERROR, иначе COMMAND_ERROR
        if "Access Denied" in msg or "Unauthorized" in msg:
            res.status = RebootStatus.AUTH_ERROR
        else:
            res.status = RebootStatus.COMMAND_ERROR
        res.message = msg
        
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

def send_reboot_command(host: str, delay: int) -> tuple[bool, str]:
    """
    Отправляет команду перезагрузки через WinRM.
    Возвращает (Успех, Сообщение).
    """
    #NOTE:WARN: !!!ИСПОЛЬЗУЕТСЯ АУТЕНТИФИКАЦИЯ ПРОФИЛЯ ОТ КОТОРОГО ЗАПУЩЕНА ПРОГРАММА (надо АДМ)
    try:
        # Создаем сессию. 
        # transport='ntlm' или 'kerberos'. Если в домене, kerberos предпочтительнее.
        # Если не указывать username/password, pywinrm попробует использовать текущую сессию Windows.
        session = winrm.Session(host, auth=('dummy', 'dummy'), transport='ntlm') 
        # Примечание: для Kerberos часто достаточно просто winrm.Session(host) без auth, 
        # но для надежности теста начнем с явного указания транспорта.

        # Формируем команду PowerShell для выполнения shutdown
        cmd = f"shutdown /r /t {delay} /f"

        # Выполняем команду
        response = session.run_ps(cmd)
        
        if response.status_code == 0:
            return True, "Command sent successfully"
        else:
            # Декодируем ошибку из stderr
            error_msg = response.std_err.decode('utf-8', errors='ignore')
            return False, f"WinRM Error: {error_msg}"
            
    except Exception as e:
        return False, f"Connection/Auth Error: {str(e)}"


if __name__ == "__main__":
    # Тест с заведомо недоступным хостом
    print(check_winrm_port("DEAD-PC-999"))  
    print(check_winrm_port("localhost"))    
    print(check_winrm_port("WS-K534D"))     