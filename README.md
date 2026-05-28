# User Wallets API

REST API для управления кошельками пользователей с поддержкой конкурентных транзакций.

## 📋 Возможности

- Создание кошельков с уникальными UUID
- Пополнение (DEPOSIT) и снятие (WITHDRAW) средств
- Обработка конкурентных запросов без потери денег (SELECT ... FOR UPDATE)
- Полное покрытие тестами (включая тесты конкурентности)
- Docker Compose – одна команда для запуска
- Асинхронный код (FastAPI + asyncpg)
- PEP8 (black, isort, flake8)
- Миграции БД (Alembic)
- Swagger UI документация

## 🛠️ Технологический стек

- **FastAPI** – асинхронный веб-фреймворк
- **PostgreSQL** + **asyncpg** – база данных
- **SQLAlchemy 2.0** – асинхронная ORM
- **Alembic** – миграции
- **pytest** + **pytest-asyncio** – тесты
- **Docker** / **Docker Compose** – контейнеризация

## 🚀 Быстрый старт (Docker)

```bash
git clone https://github.com/kiptone/user-wallets-api.git
cd user_wallets
docker-compose up -d
Приложение доступно на http://localhost:8000
Swagger UI: http://localhost:8000/docs

📚 API примеры
Создать кошелёк

curl -X POST http://localhost:8000/api/v1/wallets

Получить баланс

curl http://localhost:8000/api/v1/wallets/{wallet_id}

Пополнить

curl -X POST http://localhost:8000/api/v1/wallets/{wallet_id}/operation \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "DEPOSIT", "amount": 1000}'

Снять

curl -X POST http://localhost:8000/api/v1/wallets/{wallet_id}/operation \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "WITHDRAW", "amount": 300}'


🔒 Обработка конкурентности
Используется пессимистическая блокировка на уровне БД – SELECT ... FOR UPDATE.
Даже при 100 одновременных запросах к одному кошельку операции выполняются последовательно, баланс не теряется и не уходит в минус.

🧪 Тестирование

pytest tests/ -v
# Только тесты конкурентности
pytest tests/test_wallets.py::TestConcurrency -v
📝 Code Quality

black --check app tests
isort --check-only app tests
flake8 app tests


---
