from core.models import RebootTask, RebootResult, RebootStatus

task = RebootTask(
    host="WS-K534D",
    run_id="run-0001"
)

result = RebootResult(
    host=task.host,
    run_id=task.run_id,
    status=RebootStatus.PENDING,
    message="Задача создана. Reboot ещё не отправлялся.",
    dry_run=task.dry_run,
    method=task.method
)

print(task)
print(result)
print(result.status.value)