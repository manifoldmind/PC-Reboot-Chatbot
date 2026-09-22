import sys
import argparse
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.models import RebootTask, RebootStatus
from core.reboot import process_task
from core.logger import log_result
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()  # Загружает переменные из .env файла рядом с .exe

def load_allowed_hosts(file_path: str = "allowed_hosts.txt") -> set[str]:
    """Загружает белый список хостов из файла."""
    allowed = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                host = line.strip().upper()
                if host and not host.startswith('#'):
                    allowed.add(host)
    except FileNotFoundError:
        print(f"Предупреждение: файл {file_path} не найден. Белый список пуст.")
    return allowed


ALLOWED_HOSTS = load_allowed_hosts()


def parse_args():
    parser = argparse.ArgumentParser(description="PCReboot CLI")
    #HOLD: parser.add_argument("--hosts", type=str, help="Список хостов через запятую")
    parser.add_argument("--hosts", nargs='+', type=str, help="Список хостов через пробел")
    parser.add_argument("--file", type=str, help="Путь к файлу со списком хостов")
    parser.add_argument("--dry-run", action="store_true", help="Режим проверки")
    parser.add_argument("--oarm", action="store_true", help="Использовать OARM-скрипт (автосохранение Office)")
    parser.add_argument("--email", type=str, help="Email пользователя для получения списка ПК из Naumen")
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


def create_tasks(hosts_list: list[str], run_id: str, dry_run: bool, oarm: bool) -> list[RebootTask]:
    """Превращает список строк в список объектов RebootTask."""
    tasks = []
    for host in hosts_list:
        task = RebootTask(
            host=host.upper(),
            run_id=run_id,
            dry_run=dry_run,
            oarm=oarm
        )
        tasks.append(task)
    return tasks


def main():    
    args = parse_args()
    # ... остальной код
    args = parse_args()
    hosts_list = []

    # 1. Если указан email, получаем список из Naumen
    if args.email:
        from core.naumen import get_naumen_client
        print(f"🔍 Запрос активов Naumen для пользователя: {args.email}...")
        
        client = get_naumen_client()
        naumen_hosts = client.get_user_assets_by_email(args.email)
        
        if not naumen_hosts:
            print(f"⚠️ В Naumen не найдено ПК для пользователя {args.email}.")
            sys.exit(1)
            
        print(f"✅ Naumen вернул {len(naumen_hosts)} хостов, закрепленных за пользователем:")
        for i, host in enumerate(naumen_hosts, 1):
            print(f"   {i}. {host}")
        
        # Если при этом передан --hosts, делаем пересечение (безопасная перезагрузка)
        if args.hosts:
            requested = set(h.strip().upper() for h in args.hosts)
            hosts_list = [h for h in naumen_hosts if h in requested]
            
            if not hosts_list:
                print(f"\n❌ Ошибка: Ни один из запрошенных хостов не принадлежит пользователю {args.email}.")
                sys.exit(1)
                
            print(f"\n🎯 К перезагрузке допущены (прошли проверку прав): {', '.join(hosts_list)}")
            # Продолжаем выполнение (идем дальше к create_tasks)
            
        else:
            # Если --hosts НЕ передан, это режим ИНВЕНТАРИЗАЦИИ.
            # Мы просто выводим список и завершаем работу, ничего не перезагружая!
            print(f"\n💡 Режим инвентаризации. Перезагрузка не выполнена.")
            print(f"Чтобы перезагрузить конкретный ПК, используйте команду:")
            print(f"   PCReboot.exe --email {args.email} --hosts <ИМЯ_ПК>")
            sys.exit(0) # Чистый выход без ошибок

    # 2. Если email не указан, работаем по старой схеме (--hosts или --file)
    elif args.hosts:
        hosts_list = [h.strip().upper() for h in args.hosts if h.strip()]
    elif args.file:
        hosts_list = [h.strip().upper() for h in load_hosts_from_file(args.file)]
    else:
        print("Ошибка: необходимо указать --email, --hosts или --file")
        sys.exit(1)

    if not hosts_list:
        print("Ошибка: итоговый список хостов пуст.")
        sys.exit(1)

    run_id = datetime.now().strftime("run-%Y%m%d-%H%M%S")
    mode_str = "OARM" if args.oarm else "STANDARD"
    print(f"Запуск режима: {'DRY-RUN' if args.dry_run else 'REAL'} [{mode_str}]")
    print(f"Найдено хостов: {len(hosts_list)}")
    print("-" * 30)

    tasks = create_tasks(hosts_list, run_id, args.dry_run, args.oarm)
    max_tasks = min(5, len(tasks))
    print(f"Обработка {len(tasks)} задач в {max_tasks} потока...")
    print("-" * 30)

    results = []
    with ThreadPoolExecutor(max_workers=max_tasks) as executor:
        future_to_task = {
            executor.submit(process_task, task, ALLOWED_HOSTS): task
            for task in tasks
        }
        for future in as_completed(future_to_task):
            result = future.result()
            log_result(result)
            results.append(result)
            print(f"[{result.status.value}] {result.host}: {result.message}")

    print("\n" + "=" * 40)
    print("ИТОГОВАЯ СВОДКА")
    print("=" * 40)
    print(f"Всего обработано: {len(results)}")
    status_counts = Counter(result.status.value for result in results)
    for status, count in status_counts.items():
        print(f"{status}: {count}")

    GOOD_STATUSES = (
        RebootStatus.SKIPPED,
        RebootStatus.COMMAND_SENT,
        RebootStatus.REBOOT_CONFIRMED
    )
    failed_results = [r for r in results if r.status not in GOOD_STATUSES]
    if failed_results:
        print("\nТРЕБУЮТ ВНИМАНИЯ:")
        for r in failed_results:
            print(f" - {r.host}: {r.status.value} ({r.message})")
    else:
        print("\nВсе задачи выполнены успешно!")


if __name__ == "__main__":
    main()