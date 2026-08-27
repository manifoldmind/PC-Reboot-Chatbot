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
        
        
    #SOLVED:    
    # Далее - Как идентифицируем в Naumen пользователя, который обращается как клиент?
    def get_user_assets_by_email(self, user_identifier: str) -> List[str]:
        """
        Возвращает список hostname'ов (в верхнем регистре), 
        принадлежащих организации и соответствующих правилам валидации.
        """
        if self.use_mock:
            return self._mock_get_assets(user_identifier)
        
        # --- РЕАЛЬНЫЙ ЗАПРОС К NAUMEN API (Структура по официальной документации) ---
        try:
            # WARN :TODO: Виртуальные машины (Virtual User Machine) и Linux (RedOS) 
            # могут иметь атрибут title без домена (например, "win10-1234" или "redos-5678").
            # В версии v2.1 необходимо добавить логику:
            # 1. Запрашивать атрибут 'model' или 'type' (например, "Virtual User Machine").
            # 2. Если это ВМ или Linux, применять альтернативные правила валидации title 
            #    (например, проверка по внутреннему реестру имен или суффиксам).
            # Пока мы строго фильтруем только по наличию суффикса ".nsd.ru".

            # Запрашиваем UUID, title и organization. 
            # attrs ограничивает выдачу, защищая от 504 ошибки.
            params = {
                "accessKey": self.access_key,
                "limit": 1000,  # Безопасный лимит
                "attrs": "UUID,title,organization"
            }

            # FQN для конфигурационных единиц в Naumen обычно cmdb$ci
            fqn = "cmdb$ci"
            
            # Фильтр в формате JSON, как в документации Naumen.
            # Примечание: возможно, потребуется 'employee.email' вместо 'employee.login', 
            # уточни это по результатам Postman-теста.
            filter_json = f'{{"employee.login": "{user_identifier}"}}'
            
            # URL-кодируем фильтр, чтобы избежать проблем с символами { } " :
            # encoded_filter = urllib.parse.quote(filter_json)
            
            # Формируем URL согласно документации: /find/{fqn}/{filter}?params...
            endpoint = f"{self.base_url}/services/rest/find/{fqn}"
            
            # Параметры для защиты от 504 ошибки (строго по документации!)
            params = {
                "accessKey": self.access_key,
                "limit": 100,  # Ограничиваем выдачу
                "attrs": "UUID,title,organization"
            }
            
            response = requests.get(
                endpoint,
                params=params,
                timeout=15,
                verify=False # Отключаем проверку SSL для внутренних корпоративных сертификатов
            )
            
            
            
            # Отключаем предупреждения о небезопасном запросе (т.к. verify=False)
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            response.raise_for_status()
            data = response.json()

            # Naumen возвращает список объектов. Извлекаем поле 'title' (это hostname)
            hostnames = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                
                title = str(item.get('title', '')).strip().upper()
                org_id = str(item.get('organization', {}).get('id', '')).strip()
                
                # Проверка домена - строго nsd.ru
                if title.endswith('.NSD.RU'):
                    continue
                
                # 2. Проверка организации
                # В Naumen поле organization может быть числом (2539408) или ссылкой (UUID/словарь).
                # Если это число, проверяем напрямую. Если ссылка, пока пропускаем проверку, 
                # полагаясь на то, что токен ТУЗ уже ограничен этой организацией.
                is_valid_org = False
                if isinstance(org_id, str) and org_id.isdigit():
                    is_valid_org = (int(org_id) == self.expected_org_id)
                    
                if is_valid_org:
                    hostnames.append(title.upper())
            # Удаляем дубликаты, если они вдруг попались, и сортируем для порядка
            return sorted(list(set(hostnames)))

        
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при запросе к Naumen API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Ответ сервера (статус {e.response.status_code}): {e.response.text[:200]}")
            return []
        
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

