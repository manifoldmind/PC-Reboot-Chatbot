"""
Интеграция с Naumen CMDB.
Пока использует заглушку (Mock) для демонстрации логики.
"""

from typing import List
import requests
import os
import urllib

class NaumenClient:
    # Обязательные поля, без которых нет смысла в классе
    def __init__(self, base_url: str, token: str, use_mock: bool = True):
        """
        :param base_url: Базовый URL API Naumen
        :param token: Токен авторизации технической учетной записи
        :param use_mock: Если True, использует тестовые данные вместо реального запроса
        """
        self.base_url = base_url.rstrip('/') # "https://sd.moex.com/sd/operator"
        self.token = token
        self.use_mock = use_mock
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # Ожидаемый ID организации из SQL-запроса
        self.expected_org_id = 2539408
        
    # ============================================================
    # ПУБЛИЧНЫЙ МЕТОД
    # ============================================================    
    #SOLVED:    
    # Далее - Как идентифицируем в Naumen пользователя, который обращается как клиент?
    def get_user_assets_by_email(self, user_email: str) -> List[str]:
        """
        Возвращает список hostname'ов (в верхнем регистре), 
        принадлежащих организации и соответствующих правилам валидации.
        """
        #STUB:
        if self.use_mock:
            return self._mock_get_assets(user_email)
        
        # --- РЕАЛЬНЫЙ ЗАПРОС К NAUMEN API (Структура по официальной документации) ---
        # ШАГ 1: Найти UUID сотрудника по email
        employee_uuid = self._find_employee_uuid_by_email(user_email)
        if not employee_uuid:
            print(f"⚠️ Сотрудник с email '{user_email}' не найден в Naumen.")
            return []

        print(f"✅ Найден сотрудник UUID: {employee_uuid}")

        # ШАГ 2: Найти ПК этого сотрудника
        return self._find_computers_by_employee(employee_uuid)
    
    # ============================================================
    # ШАГ 1: Поиск UUID сотрудника по email
    # ============================================================
        # ============================================================
    # ШАГ 1: Поиск UUID сотрудника по email
    # ============================================================
    def _find_employee_uuid_by_email(self, user_email: str) -> str | None:
        """
        Ищет UUID сотрудника по его email.
        В Naumen email хранится в объекте 'account', связанном с 'employee'.
        Пробуем несколько вариантов FQN, т.к. точное название зависит от настройки.
        """
        # Варианты FQN для поиска (от наиболее вероятного к менее)
        # В SQL-запросе видно: tbl_account имеет поле 'email' и ссылку 'employee'
        candidate_fqns = [
            "account",           # tbl_account
            "employee",          # tbl_employee (если email хранится прямо там)
            "account$employee",  # возможный кастомный FQN
        ]

        for fqn in candidate_fqns:
            try:
                # Фильтр по email
                filter_json = f'{{"email": "{user_email}"}}'
                encoded_filter = urllib.parse.quote(filter_json)

                endpoint = f"{self.base_url}/services/rest/find/{fqn}/{encoded_filter}"
                params = {
                    "accessKey": self.access_key,
                    "limit": 1,
                    "attrs": "UUID,email,employee"
                }

                response = requests.get(
                    endpoint,
                    params=params,
                    timeout=10,
                    verify=False
                )
                response.raise_for_status()
                data = response.json()

                if data and isinstance(data, list) and len(data) > 0:
                    item = data[0]
                    # Если нашли сразу в account — берём поле 'employee' (ссылка на сотрудника)
                    employee_ref = item.get('employee')
                    if isinstance(employee_ref, dict) and 'UUID' in employee_ref:
                        return employee_ref['UUID']
                    elif isinstance(employee_ref, str):
                        return employee_ref
                    # Если email прямо в employee — берём UUID самого объекта
                    elif 'UUID' in item:
                        return item['UUID']

            except requests.exceptions.RequestException as e:
                print(f"  Пробуем следующий FQN после ошибки на '{fqn}': {e}")
                continue

        print(f" Не удалось найти сотрудника по email '{user_email}' ни в одном из FQN.")
        return None
    
    # ============================================================
    # ШАГ 2: Поиск ПК по UUID сотрудника
    # ============================================================
    def _find_computers_by_employee(self, employee_uuid: str) -> List[str]:
        """
        Ищет все ПК/ВМ, где поле 'employee' ссылается на заданный UUID.
        Фильтрует по организации и домену .nsd.ru.
        """
        try:
            fqn = "cmdb$ci"

            # Фильтр: employee = UUID сотрудника
            filter_json = f'{{"employee": "{employee_uuid}"}}'
            encoded_filter = urllib.parse.quote(filter_json)

            endpoint = f"{self.base_url}/services/rest/find/{fqn}/{encoded_filter}"

            params = {
                "accessKey": self.access_key,
                "limit": 1000,
                "attrs": "UUID,title,organization,classification"
            }

            response = requests.get(
                endpoint,
                params=params,
                timeout=15,
                verify=False
            )
            response.raise_for_status()
            data = response.json()

            hostnames = []
            for item in data:
                if not isinstance(item, dict):
                    continue

                title = str(item.get('title', '')).strip().upper()
                org_data = item.get('organization', {})

                # !WARN: Пропускаем хосты БЕЗ домена .nsd.ru
                if not title.endswith('.NSD.RU'):
                    continue

                # Проверка организации
                is_valid_org = self._check_organization(org_data)

                # !TODO v2.1: Виртуальные машины (Virtual User Machine) и Linux (RedOS)
                # могут иметь title БЕЗ домена (например, "win10-1234" или "redos-5678").
                # Необходимо:
                # 1. Запрашивать атрибут 'model' или 'type' или 'classification'.
                # 2. Если это ВМ/ Linux — применять альтернативные правила валидации
                #    (проверка по внутреннему реестру имён или суффиксам).
                # 3. Возможно, использовать поле 'classification' (в SQL: b."classification" = 2761404)
                #    для фильтрации только нужных типов устройств.

                if is_valid_org and title:
                    hostnames.append(title)

            return sorted(list(set(hostnames)))

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе ПК сотрудника: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Статус {e.response.status_code}: {e.response.text[:200]}")
            return []
    
    # ============================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ============================================================
    def _check_organization(self, org_data) -> bool:
        """Проверяет, что ПК принадлежит нужной организации."""
        if isinstance(org_data, dict):
            org_id_str = str(org_data.get('id', '')).strip()
            if org_id_str.isdigit():
                return int(org_id_str) == self.expected_org_id
            # Если org_data содержит UUID — пока доверяем (токен ТУЗ ограничен)
            return True
        elif isinstance(org_data, int):
            return org_data == self.expected_org_id
        else:
            # Если organization не пришла (нет прав на атрибут) — доверяем домену
            return True

    #STUB-TEST:
    def _mock_get_assets(self, user_identifier: str) -> List[str]:
        """
        Заглушка для демонстрации логики.
        Возвращает список hostname'ов (в верхнем регистре), 
        закрепленных за пользователем (по login или email).
        """
        mock_db = {
            "test.user@nsd.ru": ["OARM-1224.NSD.RU", "OARM-1532.NSD.RU", "WIN10-TEST.NSD.RU"], 
        }
        
        return [targ_host.upper() for targ_host in mock_db.get(user_identifier.lower(), [])]
            
def get_naumen_client() -> NaumenClient:
    """
    Создает и возвращает экземпляр NaumenClient с настройками из переменных окружения.
    """
    url = os.getenv("NAUMEN_BASE_URL", "https://sd.moex.com/sd")
    token = os.getenv("NAUMEN_TOKEN", "mock-access-key-12345")
    use_mock = os.getenv("NAUMEN_USE_MOCK", "True").lower() == "true"
    # WARN: use_mock=False означает, что теперь идут РЕАЛЬНЫЕ запросы к Naumen!
    # Убедись, что переменная окружения NAUMEN_API_TOKEN установлена корректно.
    return NaumenClient(base_url=url, token=token, use_mock=use_mock)

