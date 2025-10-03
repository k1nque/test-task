# Краткое руководство по развертыванию

## Вариант 1: Docker (Рекомендуется)

### Требования
- Docker 20.10+
- Docker Compose 1.29+

### Шаги

1. **Клонируйте проект**
   ```bash
   git clone <repository-url>
   cd test-task
   ```

2. **Настройте окружение**
   ```bash
   cp .env.example .env
   # Отредактируйте .env при необходимости
   ```

3. **Запустите проект**
   ```bash
   # Используя скрипт (Linux/macOS)
   ./start.sh
   
   # Или напрямую через Docker Compose
   docker-compose up -d --build
   
   # Или через Makefile
   make up
   ```

4. **Проверьте работу**
   - API: http://localhost:8000
   - Swagger: http://localhost:8000/docs
   - Redoc: http://localhost:8000/redoc

5. **Остановите проект**
   ```bash
   # Используя скрипт
   ./stop.sh
   
   # Или через Docker Compose
   docker-compose down
   
   # Или через Makefile
   make down
   ```

## Вариант 2: Локальная установка

### Требования
- Python 3.11+
- PostgreSQL 15+ с PostGIS
- UV package manager

### Шаги

1. **Установите зависимости**
   ```bash
   # Установите UV
   pip install uv
   
   # Установите зависимости проекта
   uv pip install -r pyproject.toml
   ```

2. **Настройте базу данных**
   ```bash
   # Создайте базу данных
   createdb organizations_db
   
   # Установите PostGIS
   psql organizations_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   ```

3. **Настройте окружение**
   ```bash
   cp .env.example .env
   # Отредактируйте .env с параметрами подключения к БД
   ```

4. **Примените миграции**
   ```bash
   alembic upgrade head
   ```

5. **Заполните тестовыми данными**
   ```bash
   python scripts/seed_data.py
   ```

6. **Запустите сервер**
   ```bash
   # Режим разработки
   uvicorn main:app --reload
   
   # Или
   python main.py
   
   # Или через Makefile
   make dev
   ```

## Тестирование API

### С использованием curl

```bash
# Установите API ключ
export API_KEY="your-secret-api-key-change-in-production"

# Получите список организаций
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/organizations/

# Получите дерево деятельностей
curl -H "X-API-Key: $API_KEY" http://localhost:8000/api/v1/activities/tree
```

### Через Swagger UI

1. Откройте http://localhost:8000/docs
2. Нажмите "Authorize"
3. Введите API ключ: `your-secret-api-key-change-in-production`
4. Тестируйте эндпоинты через интерфейс

## Дополнительные команды

### Docker

```bash
# Просмотр логов
docker-compose logs -f

# Просмотр логов определенного сервиса
docker-compose logs -f api

# Перезапуск сервиса
docker-compose restart api

# Подключение к контейнеру
docker-compose exec api bash

# Подключение к PostgreSQL
docker-compose exec db psql -U postgres -d organizations_db
```

### Makefile (если установлен make)

```bash
make help          # Показать все доступные команды
make up            # Запустить проект
make down          # Остановить проект
make logs          # Показать логи
make shell         # Открыть shell в контейнере API
make db-shell      # Открыть PostgreSQL shell
make migrate       # Применить миграции
make seed          # Заполнить БД данными
```

## Troubleshooting

### Порты заняты

**PostgreSQL порт 5432 занят:**

Проект по умолчанию пробрасывает PostgreSQL на внешний порт 5434, чтобы избежать конфликта с локальным PostgreSQL на порту 5432.

Для подключения к БД извне контейнера используйте:
```bash
psql -h localhost -p 5434 -U postgres -d organizations_db
```

Если порт 8000 занят, измените в `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "8001:8000"  # Измените внешний порт
```

### Ошибки миграций

```bash
# Сбросьте базу данных и примените миграции заново
docker-compose down -v
docker-compose up -d
```

### Проблемы с зависимостями

```bash
# Пересоберите контейнер
docker-compose up -d --build --force-recreate
```

## Полезные ссылки

- [Документация FastAPI](https://fastapi.tiangolo.com/)
- [Документация SQLAlchemy](https://docs.sqlalchemy.org/)
- [Документация PostGIS](https://postgis.net/documentation/)
- [Документация UV](https://github.com/astral-sh/uv)
