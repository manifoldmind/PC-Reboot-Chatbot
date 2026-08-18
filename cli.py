import sys
from core.models import RebootTask, RebootStatus
# Импортируем нашу функцию из предыдущего шага
# Убедись, что ты сохранила process_task в файл core/reboot.py 
# или временно импортируй её прямо здесь для теста, если ещё не выносила.
from core.reboot import process_task     
import argparse

#STUB:
ALLOWED_HOSTS = {"WS-K534D", "WS-K534F"} # Пока захардкодим белый список
def parse_args():
    parser = argparse.ArgumentParser(description="PCReboot CLI v2.0")
    
    # Аргумент для списка хостов
    parser.add_argument(
        "--hosts", 
        type=str, 
        help="Список хостов через запятую (например: PC-01,PC-02)"
    )
    
    # Флаг dry-run
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Режим проверки без реальной перезагрузки"
    )

    return parser.parse_args()

def create_tasks(hosts_str: str, run_id: str, dry_run: bool) -> list[RebootTask]:
    """Список хостов -> список объектов RebootTask"""
    
    if not hosts_str:
        return []
    
    tasks = []
    hosts_list = [host for host in hosts_str.split(' ')]
    
    for host in hosts_list:
        task = RebootTask(
            host=host.upper(), 
            run_id=run_id,
            dry_run=dry_run
        )
        tasks.append(task)
        
    return tasks

def main():
    args = parse_args()
    
    if not args.hosts:
        print("Ошибка: необходимо указать хотя бы один хост через --hosts")
        sys.exit(1)
        
    #STUB:
    run_id = "manual-run-001" # Пока статический ID
    
    print(f"Запуск режима: {'DRY-RUN' if args.dry_run else 'REAL'}")
    print(f"Целевые хосты: {args.hosts}")
    print("-" * 30)

    # 1. Создаем задачи
    tasks = create_tasks(args.hosts, run_id, args.dry_run)
    
    # 2. Обрабатываем каждую задачу через ядро
    for task in tasks:
        result = process_task(task, ALLOWED_HOSTS)
        
        # 3. Выводим результат
        print(f"[{result.status.value}] {result.host}: {result.message}")

if __name__ == "__main__":
    main()
        


# Далее журнал запускающихся тасок...