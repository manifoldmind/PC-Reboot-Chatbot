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
        
    #SOLVED:    
    # Далее - Как идентифицируем в Naumen пользователя, который обращается как клиент?
    def get_user_assets_by_email(self, user_identifier: str) -> List[str]:
        """
        Возвращает список hostname'ов (в верхнем регистре), 
        закрепленных за пользователем (по login или email).
        """
        if self.use_mock:
            return self._mock_get_assets(user_identifier)
        
        # --- РЕАЛЬНЫЙ ЗАПРОС К NAUMEN API (Структура по официальной документации) ---
        try:
            # FQN для конфигурационных единиц в Naumen обычно cmdb$ci
            fqn = "cmdb$ci"
            
            # Фильтр в формате JSON, как в документации Naumen.
            # Примечание: возможно, потребуется 'employee.email' вместо 'employee.login', 
            # уточни это по результатам Postman-теста.
            filter_json = f'{{"employee.login": "{user_identifier}"}}'
            
            # URL-кодируем фильтр, чтобы избежать проблем с символами { } " :
            encoded_filter = urllib.parse.quote(filter_json)
            
            # Формируем URL согласно документации: /find/{fqn}/{filter}?params...
            endpoint = f"{self.base_url}/services/rest/find/{fqn}/{encoded_filter}"
            
            # Параметры для защиты от 504 ошибки (строго по документации!)
            params = {
                "accessKey": self.access_key,
                "limit": 100,  # Ограничиваем выдачу
                "attrs": "title,employee.login,employee.email" #WARN:TODO: уточнить employee.login vs employee.email или еще что
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
                if isinstance(item, dict) and "title" in item:
                    hostnames.append(item["title"].upper())
                    
            return hostnames
        
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
    
    return NaumenClient(base_url=url, token=token, use_mock=use_mock)

