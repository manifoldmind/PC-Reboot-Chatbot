"""
Интеграция с Naumen CMDB.
Пока использует заглушку (Mock) для демонстрации логики.
"""

from typing import List
import requests
import os

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
            "Accept": "aplication/json"
        }
        
        
    # Далее - QUE:PROC:Как идентифицируем в Naumen пользователя, который обращается как клиент?
    def get_user_assets_by_email(self, user_email: str) -> List[str]:
        """
        Возвращает список hostname'ов (в верхнем регистре), 
        закрепленных за пользователем с данным email.
        """
        if self.use_mock:
            return self._mock_get_assets(user_email)
        
        # --- РЕАЛЬНЫЙ ЗАПРОС К NAUMEN API (Структура по официальной документации) ---
        try:
            # FQN (Fully Qualified Name) класса объекта. 
            # Обычно это 'cmdb.ci' (все конфигурационные единицы) или 'cmdb.computer'
            fqn = "cmdb.ci" 
            
            # Фильтр по email владельца и типу устройства (Computer или Virtual Machine)
            # В Naumen это часто передается прямо в пути или как параметры запроса
            endpoint = f"{self.base_url}/find/{fqn}"
            


        
        
