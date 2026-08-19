import sys
import argparse
from pathlib import Path
from core.models import RebootTask, RebootStatus
from core.reboot import process_task
from core.logger import log_result
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

# STUB: Пока захардкодим белый список
ALLOWED_HOSTS = {"WS-K534D", "WS-K534F"} 

def parse_args():
    parser = argparse.ArgumentParser(description="PCReboot CLI v2.0")
    
    # Аргумент для списка хостов
    parser.add_argument(
        "--hosts", 
        type=str, 
        help="Список хостов через запятую (например: PC-01,PC-02)"
    )
    
    # Аргумент для файла со списком
    parser.add_argument(
        "--file",
        type=str,
        help="Путь к файлу со списком хостов (по одному на строку)"
    )
    
    # Флаг dry-run
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Режим проверки без реальной перезагрузки"
    )

    return parser.parse_args()

def load_hosts_from_file(file_path: str) -> list[str]:
    """Читает хосты из файла, игнорируя пустые строки."""
    path = Path(file_path)
    if not path.exists():
        print(f"Ошибка: файл {file_path} не найден.")
        sys.exit(1)
        
    hosts = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            host = line.strip()
            if host:
                hosts.append(host)
    return hosts

def create_tasks(hosts_list: list[str], run_id: str, dry_run: bool) -> list[RebootTask]:
    """Превращает список строк в список объектов RebootTask."""
    tasks = []
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
    
    hosts_list = []
    
    # 1. Определяем источник хостов
    if args.hosts:
        # Если передан --hosts, разбиваем строку по запятой
        hosts_list = [h.strip() for h in args.hosts.split(",") if h.strip()]
    elif args.file:
        # Если передан --file, читаем из файла
        hosts_list = load_hosts_from_file(args.file)
    else:
        print("Ошибка: необходимо указать хосты через --hosts или --file")
        sys.exit(1)

    if not hosts_list:
        print("Ошибка: список хостов пуст.")
        sys.exit(1)

    # STUB:
    run_id = "manual-run-001" 
    
    print(f"Запуск режима: {'DRY-RUN' if args.dry_run else 'REAL'}")
    print(f"Найдено хостов: {len(hosts_list)}")
    print("-" * 30)

    # 2. Создаем задачи
    tasks = create_tasks(hosts_list, run_id, args.dry_run)
    max_tasks = min(5, len(tasks))
    print(f"Обработка {len(tasks)} задач в {max_tasks} потока...")
    print("-" * 30)

    with ThreadPoolExecutor(max_workers=max_tasks) as executor:
        # Отдаем задачи курьерам. 
        # executor.submit возвращает "обещание" (Future), что результат скоро будет
        future_to_task = {
            executor.submit(process_task, task, ALLOWED_HOSTS): task 
            for task in tasks
        }

        # as_completed ждет, пока ЛЮБОЙ курьер вернется с результатом
        for future in as_completed(future_to_task):
            result = future.result() # Забираем готовый RebootResult у курьера
            
            # Записываем результат в ЖУРНАЛ (лог)
            log_result(result)
            
            # Выводим результат в консоль
            print(f"[{result.status.value}] {result.host}: {result.message}")

    # # 3. Обрабатываем каждую задачу через ядро
    # for task in tasks:
    #     result = process_task(task, ALLOWED_HOSTS)        
    #     # Записываем в лог
    #     log_result(result)
        
    #     # 4. Выводим результат
    #     print(f"[{result.status.value}] {result.host}: {result.message}")

if __name__ == "__main__":
    main()