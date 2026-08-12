""" Список статусов операции:
PENDING
VALIDATION_FAILED
NOT_ALLOWED
PRECHECK_FAILED
AUTH_ERROR
COMMAND_SENT
REBOOT_CONFIRMED
TIMEOUT
COMMAND_ERROR
SKIPPED
UNKNOWN_ERROR
"""

"""
Контракты данных PCReboot.

Файл описывает структуры данных, которые используются всеми слоями системы:
- CLI создаёт RebootTask;
- core обрабатывает задачу и возвращает RebootResult;
- логи/отчёты используют RebootResult;
- будущие интеграции Naumen/BotX также смогут использовать эти структуры.

Файл НЕ выполняет сетевых операций и НЕ печатает пользователю.
"""
