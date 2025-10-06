# Organizations Directory REST API

REST API приложение для справочника Организаций, Зданий и Деятельности.

## Описание

Приложение предоставляет REST API для управления справочником организаций с поддержкой:

- **Организации**: карточки организаций с номерами телефонов и видами деятельности
- **Здания**: информация о зданиях с географическими координатами
- **Деятельность**: древовидная структура видов деятельности (до 3 уровней вложенности)
- **Поиск**: различные методы поиска организаций

## Технологический стек

- **FastAPI** - веб-фреймворк
- **Pydantic** - валидация данных
- **SQLAlchemy** - ORM
- **Alembic** - миграции базы данных
- **PostgreSQL + PostGIS** - база данных с поддержкой геопространственных данных
- **Docker** - контейнеризация
- **UV** - пакетный менеджер Python

## Требования

- Docker и Docker Compose
- Или: Python 3.11+, PostgreSQL 15+ с PostGIS, UV

## Быстрый старт с Docker

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd test-task

# Скопируйте файл окружения
cp .env.example .env

# Отредактируйте .env при необходимости
# По умолчанию используется API_KEY: your-secret-api-key-change-in-production
```

### 2. Запуск приложения

#### Через helper-скрипт `start.sh`

```bash

./start.sh

```

#### Вручную через Docker Compose

```bash
# Запустите все сервисы (скрипт автоматически определит версию Docker Compose)
docker compose up --build

# Или в фоновом режиме
docker compose up -d --build

# Для старых версий Docker Compose V1 используйте:
# docker-compose up -d --build
```

Приложение будет доступно по адресу:

- API: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

**База данных:**

- PostgreSQL доступна на порту 5434 (внешний) для избежания конфликта с локальным PostgreSQL
- Подключение: `psql -h localhost -p 5434 -U postgres -d organizations_db`

### 3. Остановка приложения

```bash
# Используя скрипт
./stop.sh

# Или напрямую
docker compose down

# Для Docker Compose V1:
# docker-compose down

# С удалением данных
docker compose down -v
```

#### Makefile команды

Для удобства проект включает набор make-таргетов (см. `Makefile`):

```bash
# Запуск сервисов (аналог ./start.sh)
make up

# Просмотр логов
make logs

# Остановка
make down

# Полная очистка (контейнеры + volumes)
make clean
```

## Запуск без Docker

### 1. Установка зависимостей

```bash
# Установите UV (если еще не установлен)
pip install uv

# Установите зависимости
uv pip install -r pyproject.toml
```

### 2. Настройка базы данных

```bash
# Установите PostgreSQL с PostGIS
# Создайте базу данных
createdb organizations_db

# Примените расширение PostGIS
psql organizations_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Настройте .env файл с параметрами подключения
```

### 3. Миграции и заполнение данных

```bash
# Примените миграции
alembic upgrade head

# Заполните тестовыми данными
python scripts/seed_data.py
```

### 4. Запуск сервера

```bash
# Режим разработки
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Или через Python
python main.py
```

## API Документация

### Аутентификация

Все запросы требуют наличия заголовка `X-API-Key` с действительным API ключом.

**Пример:**

```bash
curl -H "X-API-Key: your-secret-api-key-change-in-production" \
  http://localhost:8000/api/v1/organizations/
```

### Основные эндпоинты

#### Организации

- `GET /api/v1/organizations/` - Список всех организаций
- `GET /api/v1/organizations/{id}` - Получить организацию по ID
- `POST /api/v1/organizations/` - Создать новую организацию
- `GET /api/v1/organizations/by-building/{building_id}` - Организации в здании
- `GET /api/v1/organizations/by-activity/{activity_id}` - Организации по виду деятельности (включая дочерние)
- `GET /api/v1/organizations/search/by-name?name=...` - Поиск по названию
- `POST /api/v1/organizations/search/by-location` - Поиск по геолокации

#### Здания

- `GET /api/v1/buildings/` - Список всех зданий
- `GET /api/v1/buildings/{id}` - Получить здание по ID

#### Деятельности

- `GET /api/v1/activities/` - Список всех деятельностей
- `GET /api/v1/activities/tree` - Дерево деятельностей
- `GET /api/v1/activities/{id}` - Получить деятельность с дочерними элементами

## Примеры использования

### 1. Получить все организации в здании

```bash
curl -H "X-API-Key: your-secret-api-key-change-in-production" \
  "http://localhost:8000/api/v1/organizations/by-building/1?limit=10&offset=0"
```

### 2. Поиск организаций по виду деятельности

```bash
# Поиск организаций занимающихся "Едой" (включая "Мясная продукция", "Молочная продукция")
curl -H "X-API-Key: your-secret-api-key-change-in-production" \
  "http://localhost:8000/api/v1/organizations/by-activity/1"
```

### 3. Поиск по названию

```bash
curl -H "X-API-Key: your-secret-api-key-change-in-production" \
  "http://localhost:8000/api/v1/organizations/search/by-name?name=Рога"
```

### 4. Поиск в радиусе (500 метров от точки)

```bash
curl -X POST \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 55.7558,
    "longitude": 37.6173,
    "radius_meters": 5000,
    "limit": 10,
    "offset": 0
  }' \
  "http://localhost:8000/api/v1/organizations/search/by-location"
```

### 5. Поиск в прямоугольной области

```bash
curl -X POST \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 55.7558,
    "longitude": 37.6173,
    "min_latitude": 55.7,
    "max_latitude": 55.8,
    "min_longitude": 37.5,
    "max_longitude": 37.7,
    "limit": 10,
    "offset": 0
  }' \
  "http://localhost:8000/api/v1/organizations/search/by-location"
```

### 6. Получить дерево деятельностей

```bash
curl -H "X-API-Key: your-secret-api-key-change-in-production" \
  "http://localhost:8000/api/v1/activities/tree"
```

### 7. Создать новую организацию

```bash
curl -X POST \
  -H "X-API-Key: your-secret-api-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ООО \"Новая компания\"",
    "building_id": 1,
    "phone_numbers": ["8-800-555-00-00", "8-495-123-45-67"],
    "activity_ids": [1, 2]
  }' \
  "http://localhost:8000/api/v1/organizations/"
```

## Структура проекта

```text
test-task/
├── app/
│   ├── api/              # API эндпоинты
│   │   ├── organizations.py
│   │   ├── buildings.py
│   │   └── activities.py
│   ├── core/             # Конфигурация и безопасность
│   │   ├── config.py
│   │   └── security.py
│   ├── db/               # База данных
│   │   └── session.py
│   ├── models/           # SQLAlchemy модели
│   │   └── models.py
│   └── schemas/          # Pydantic схемы
│       └── schemas.py
├── alembic/              # Миграции базы данных
│   ├── versions/
│   └── env.py
├── scripts/              # Утилиты
│   └── seed_data.py     # Скрипт заполнения данных
├── main.py               # Точка входа приложения
├── alembic.ini           # Конфигурация Alembic
├── pyproject.toml        # Зависимости проекта
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose конфигурация
└── README.md             # Документация
```

## База данных

### Схема

**Buildings** (Здания)

- id (PK)
- address (string)
- coordinates (PostGIS POINT)
- created_at, updated_at

**Activities** (Деятельность)

- id (PK)
- name (string, unique)
- parent_id (FK -> activities.id)
- level (integer, 1-3)
- created_at, updated_at

**Organizations** (Организации)

- id (PK)
- name (string)
- building_id (FK -> buildings.id)
- created_at, updated_at

**OrganizationPhone** (Телефоны организаций)

- id (PK)
- organization_id (FK -> organizations.id)
- phone_number (string)

**organization_activity** (Many-to-Many)

- organization_id (FK -> organizations.id)
- activity_id (FK -> activities.id)

## Особенности реализации

1. **Древовидная структура деятельностей**: Self-referential связи с ограничением до 3 уровней вложенности
2. **Геопространственный поиск**: Использование PostGIS для поиска в радиусе и прямоугольной области
3. **API ключ**: Статический API ключ для всех запросов через заголовок X-API-Key
4. **Swagger/ReDoc**: Автоматическая документация API
5. **Docker**: Полная контейнеризация с автоматическим созданием базы и заполнением данных

## Разработка

### Создание новой миграции

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Работа с базой данных

```bash
# Подключение к базе данных в Docker
docker-compose exec db psql -U postgres -d organizations_db

# Пересоздание базы данных
docker-compose down -v
docker-compose up -d
```

## Лицензия

MIT

## Автор

Ваше имя
