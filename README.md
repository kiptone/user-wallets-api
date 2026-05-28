# User Wallets API

REST API для управления кошельками пользователей с поддержкой конкурентных транзакций.

## 📋 Возможности

- ✅ Создание кошельков с уникальными UUID
- ✅ Пополнение (DEPOSIT) и снятие (WITHDRAW) средств
- ✅ Обработка конкурентных запросов без потери денег
- ✅ Полное покрытие тестами (включая тесты конкурентности)
- ✅ Docker и Docker Compose для одноклассного развёртывания
- ✅ Асинхронный код (FastAPI + asyncpg)
- ✅ PEP8 соответствие (black, isort, flake8)
- ✅ Миграции БД через Alembic
- ✅ Автоматическая API документация (Swagger UI)

## 🛠️ Технологический стек

- **Framework**: FastAPI (асинхронный веб-фреймворк)
- **Database**: PostgreSQL с asyncpg драйвером
- **ORM**: SQLAlchemy 2.0 с асинхронной поддержкой
- **Миграции**: Alembic
- **Тесты**: pytest + pytest-asyncio
- **Контейнеризация**: Docker + Docker Compose
- **Линтеры**: Black, isort, flake8

## 🚀 Быстрый старт

### Способ 1: Docker Compose (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repo-url>
cd user_wallets

# Запустить приложение и БД
docker-compose up -d

# Приложение будет доступно на http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Способ 2: Локальная разработка (Python 3.14.2)

```bash
# Установить зависимости
pip install -r requirements.txt

# Установить PostgreSQL локально (если нет)
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql
# Windows: https://www.postgresql.org/download/windows/

# Создать БД
createdb wallets_db

# Применить миграции
alembic upgrade head

# Запустить сервер
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Документация

### Endpoints

#### 1. Создать кошелёк
```http
POST /api/v1/wallets
```

**Ответ (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "balance": "0.00",
  "created_at": "2024-01-15T10:30:00+00:00",
  "updated_at": "2024-01-15T10:30:00+00:00"
}
```

#### 2. Получить баланс кошелька
```http
GET /api/v1/wallets/{wallet_id}
```

**Ответ (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "balance": "1000.00",
  "created_at": "2024-01-15T10:30:00+00:00",
  "updated_at": "2024-01-15T10:35:00+00:00"
}
```

#### 3. Выполнить операцию (пополнение или снятие)
```http
POST /api/v1/wallets/{wallet_id}/operation
```

**Request:**
```json
{
  "operation_type": "DEPOSIT",
  "amount": 1000.00
}
```

**Варианты operation_type:**
- `DEPOSIT` - пополнение
- `WITHDRAW` - снятие

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "new_balance": "1000.00",
  "operation_type": "DEPOSIT",
  "amount": "1000.00",
  "timestamp": "2024-01-15T10:30:00+00:00"
}
```

**Ошибки:**
- `400 Bad Request`: Недостаточно средств, некорректная сумма
- `404 Not Found`: Кошелёк не найден
- `422 Unprocessable Entity`: Некорректные данные запроса

## 🧪 Тестирование

### Запустить тесты локально
```bash
pytest tests/ -v
```

### Запустить тесты с покрытием
```bash
pytest tests/ --cov=app --cov-report=html
# Откроется report в htmlcov/index.html
```

### Тесты конкурентности
Файл `tests/test_wallets.py` включает тесты, которые проверяют корректность работы при параллельных запросах:

- `test_concurrent_deposits` - 10 одновременных пополнений
- `test_concurrent_withdrawals_with_insufficient_funds` - гонка при снятии денег
- `test_mixed_concurrent_operations` - смешанные операции (пополнение и снятие)

```bash
# Запустить только тесты конкурентности
pytest tests/test_wallets.py::TestConcurrency -v
```

## 🔒 Обработка конкурентности

Приложение использует **пессимистическую блокировку** на уровне БД для гарантии целостности:

```python
# В services.py используется SELECT ... FOR UPDATE
SELECT * FROM wallets WHERE id = ? FOR UPDATE

# Это блокирует строку в БД, предотвращая race conditions
# Даже если 100 запросов одновременно попытаются изменить баланс,
# они будут обработаны последовательно, и баланс останется корректным
```

**Пример проблемы без блокировки:**
```
Кошелёк: баланс 100
Запрос 1: читает 100, думает "хватит для 80" → обновляет на 20
Запрос 2: одновременно читает 100, думает "хватит для 90" → обновляет на 10
ПРОБЛЕМА: Оба запроса считали, что денег достаточно, но на самом деле нужно было 170!
```

**С нашей блокировкой:**
```
Запрос 1: блокирует строку, читает 100, вычитает 80 → 20, освобождает блокировку
Запрос 2: ждёт блокировку, читает 20, видит недостаточно → ошибка 400
ПРАВИЛЬНО: Очередь обработки, баланс не потерян
```

## 📝 Code Quality (PEP8)

### Проверить соответствие PEP8
```bash
# Проверка форматирования (black)
black --check app tests

# Проверка импортов (isort)
isort --check-only app tests

# Проверка линтера (flake8)
flake8 app tests

# Все вместе
make lint
```

### Автоматическое форматирование
```bash
# Форматировать все файлы
make format
```

## 📦 Структура проекта

```
user_wallets/
├── app/                          # Основной пакет приложения
│   ├── __init__.py
│   ├── main.py                   # FastAPI приложение
│   ├── config.py                 # Конфигурация (переменные окружения)
│   ├── database.py               # Асинхронное подключение к БД
│   ├── models.py                 # SQLAlchemy модели (таблица wallets)
│   ├── schemas.py                # Pydantic схемы (валидация запросов/ответов)
│   ├── services.py               # Бизнес-логика (с пессимистическим локом)
│   └── api/
│       ├── __init__.py
│       └── wallets.py            # Роутеры (REST endpoints)
│
├── migrations/                   # Alembic миграции БД
│   ├── env.py                    # Конфигурация Alembic
│   ├── script.py.mako            # Шаблон новой миграции
│   └── versions/
│       └── 001_create_wallets.py # Первая миграция (создание таблицы)
│
├── tests/                        # Тесты
│   ├── __init__.py
│   ├── conftest.py               # Фикстуры (test DB, async client, etc.)
│   └── test_wallets.py           # Тесты endpoints и конкурентности
│
├── Dockerfile                    # Docker образ приложения
├── docker-compose.yml            # Оркестрация контейнеров
├── requirements.txt              # Python зависимости
├── pyproject.toml               # Конфиг для black, isort, pytest
├── Makefile                      # Удобные команды
├── alembic.ini                   # Конфиг Alembic
├── .env                          # Переменные окружения
├── .env.example                  # Пример переменных окружения
├── .gitignore                    # Git ignore
└── README.md                     # Этот файл
```

## 🔧 Разработка

### Установить pre-commit хуки (опционально)
```bash
pip install pre-commit
pre-commit install
```

### Создать новую миграцию БД
```bash
alembic revision --autogenerate -m "Add new_column to wallets"
```

### Откатить последнюю миграцию
```bash
alembic downgrade -1
```

### Посмотреть историю миграций
```bash
alembic history
```

## 🐳 Docker команды

```bash
# Собрать образы
docker-compose build

# Запустить в фоне
docker-compose up -d

# Посмотреть логи приложения
docker-compose logs -f app

# Посмотреть статус контейнеров
docker-compose ps

# Остановить
docker-compose down

# Полная очистка (включая volumes)
docker-compose down -v
```

## ✅ Чек-лист требований

- [x] REST API с эндпоинтами DEPOSIT и WITHDRAW
- [x] Асинхронный фреймворк (FastAPI)
- [x] PostgreSQL БД
- [x] Корректная обработка конкурентности (SELECT ... FOR UPDATE)
- [x] Миграции БД (Alembic)
- [x] PEP8 соответствие (black, isort, flake8)
- [x] Тесты конкурентности в pytest
- [x] Docker контейнеризация
- [x] Docker Compose для одной команды развёртывания
- [x] Документация и примеры использования

## 📞 Примеры использования

### Через curl

```bash
# Создать кошелёк
curl -X POST http://localhost:8000/api/v1/wallets

# Получить баланс
curl http://localhost:8000/api/v1/wallets/{wallet_id}

# Пополнить кошелёк
curl -X POST http://localhost:8000/api/v1/wallets/{wallet_id}/operation \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "DEPOSIT", "amount": 1000}'

# Снять деньги
curl -X POST http://localhost:8000/api/v1/wallets/{wallet_id}/operation \
  -H "Content-Type: application/json" \
  -d '{"operation_type": "WITHDRAW", "amount": 500}'
```

### Через Python

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Создать кошелёк
        response = await client.post("http://localhost:8000/api/v1/wallets")
        wallet = response.json()
        wallet_id = wallet["id"]
        print(f"Created wallet: {wallet_id}")
        
        # Пополнить
        response = await client.post(
            f"http://localhost:8000/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": 1000}
        )
        print(f"After deposit: {response.json()['new_balance']}")
        
        # Снять
        response = await client.post(
            f"http://localhost:8000/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": 300}
        )
        print(f"After withdrawal: {response.json()['new_balance']}")

asyncio.run(main())
```

## 🤔 FAQ

**Q: Почему используется DECIMAL для баланса, а не INTEGER?**
A: DECIMAL хранит точные десятичные числа. INTEGER часто используют для копеек/центов, но DECIMAL нагляднее для примера.

**Q: Как работает пессимистическое лоирование?**
A: `SELECT ... FOR UPDATE` блокирует строку в БД, другие транзакции ждут разблокировки. Это гарантирует, что операции выполняются последовательно.

**Q: Сможет ли приложение масштабироваться?**
A: Да, за счёт асинхронности (asyncio + asyncpg). На одном сервере можно обработать 10000+ одновременных подключений. Для горизонтального масштабирования нужно несколько инстансов + балансировщик нагрузки.

**Q: Как тестировать локально?**
A: Установите PostgreSQL, создайте БД, запустите миграции и `python -m uvicorn app.main:app --reload`. Или используйте Docker Compose.

## 📄 Лицензия

MIT

## 🤝 Contributing

Contributions приветствуются! Просто откройте Pull Request.

---

**Сделано с ❤️ для управления кошельками пользователей**
