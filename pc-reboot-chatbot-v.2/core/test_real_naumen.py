"""
Тестовый скрипт для проверки модуля Naumen.
Запускать из корня проекта: python test_real_naumen.py
"""
from naumen import get_naumen_client

def main():
    print("🔍 Инициализация клиента Naumen...")
    client = get_naumen_client()
    
    if client.use_mock:
        print("⚠️ ВНИМАНИЕ: Работает режим ЗАГЛУШКИ (MOCK).")
        print("Чтобы сделать реальный запрос, установи переменную окружения:")
        print('$env:NAUMEN_USE_MOCK = "False"')
        print('$env:NAUMEN_TOKEN = "твой_реальный_токен"\n')
    else:
        print("✅ Работает режим РЕАЛЬНОГО API.\n")

    print("Запрос активов для пользователя: test.user@nsd.ru")
    hosts = client.get_user_assets_by_email("test.user@nsd.ru")
    
    print(f"\n🎯 Найдено валидных хостов (.nsd.ru): {len(hosts)}")
    if hosts:
        print("Список хостов:")
        for h in hosts:
            print(f"  - {h}")
    else:
        print("Список пуст.")

if __name__ == "__main__":
    main()