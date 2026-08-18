from .models import RebootTask, RebootResult, RebootStatus
from datetime import datetime

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