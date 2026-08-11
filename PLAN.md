1) [x] Составить архитектуру
![[Pasted image 20260811125236.png]]

![[mermaid-1786441992150.png]]
	flowchart TD
    User["👤 Пользователь"]
    Express["📨 express.nsd.ru (аккаунт «Валера»)"]
    Service["🧠 НАШ СЕРВИС: FastAPI + pybotx + FSM"]
    AD["🔐 AD: домен, svc-аккаунт, GPO"]
    PC["💻 Целевые ПК"]

    subgraph Naumen["🗂 Naumen (ITSM)"]
        CMDB["📦 CMDB (БД)"]
    end

    User -- "нажимает серию кнопок" --> Express
    Express -- "ответ Валеры" --> User
    Express -- "webhook [JSON]: команды из кнопок" --> Service
    Service -- "REST API [JSON]: отправка сообщений/кнопок" --> Express
    Service -- "REST JSON: GET /api/assets/by_user" --> CMDB
    CMDB -- "ПК есть/нет (список/ошибка)" --> Service
    Service -- "SOAP/REST: создать/закрыть тикет (имена уточнить)" --> Naumen
    Naumen -- "№ тикета / статус" --> Service
    Service -- "WinRM/SSH: shutdown /r /t 5 /f" --> PC
    Service -. "предъявляет svc-аккаунт" .-> AD
    PC -. "Kerberos/NTLM: проверка svc-аккаунта" .-> AD
    AD -. "GPO: WinRM? файрвол? права? (вопросы админам)" .-> PC
    AD -. "синхронизация (НЕ наше дело)" .-> CMDB

2) [ ] Решить, кто именно будет сервером для нашего сервиса PC-Reboot и как (вирт станция, пк и т.д....)
3) [ ] ВОПРОСЫ: имена методов Naumen; CMDB внутри/снаружи Naumen; webhook-URL и «домик»; svc-аккаунт и GPO; порты до подсетей ПК.