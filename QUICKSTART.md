# Quick Start Guide

## Самый быстрый способ запустить проект (30 секунд)

### Требования
- Docker Desktop установлен и запущен

**Примечание:** Скрипты автоматически определят версию Docker Compose:
- Docker Compose V2: `docker compose` (рекомендуется)  
- Docker Compose V1: `docker-compose` (legacy)

### Шаги

```bash
# 1. Перейдите в директорию проекта
cd /path/to/test-task

# 2. Запустите проект
./start.sh

# 3. Откройте браузер
# Swagger UI: http://localhost:8000/docs
```

**Важно:** PostgreSQL доступен на порту **5434** (не 5432), чтобы избежать конфликта с локальным PostgreSQL.

### Тестирование API

1. В Swagger UI нажмите кнопку **"Authorize"**
2. Введите API ключ: `your-secret-api-key-change-in-production`
3. Нажмите **"Authorize"**, затем **"Close"**
4. Попробуйте любой эндпоинт, например:
   - GET `/api/v1/organizations/` - список всех организаций
   - GET `/api/v1/activities/tree` - дерево деятельностей
   - GET `/api/v1/organizations/by-building/1` - организации в здании

### Остановка

```bash
./stop.sh
```

## Альтернативные команды

### С Docker Compose
```bash
# Запуск
docker-compose up -d --build

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### С Makefile
```bash
# Запуск
make up

# Просмотр логов
make logs

# Остановка
make down

# Полная очистка
make clean
```

## Тестовые запросы с curl

```bash
# Установите переменные
export API_KEY="your-secret-api-key-change-in-production"
export BASE_URL="http://localhost:8000/api/v1"

# Получить все организации
curl -H "X-API-Key: $API_KEY" "$BASE_URL/organizations/"

# Поиск организаций в радиусе 5км от центра Москвы
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 55.7558,
    "longitude": 37.6173,
    "radius_meters": 5000,
    "limit": 10
  }' \
  "$BASE_URL/organizations/search/by-location"

# Получить дерево деятельностей
curl -H "X-API-Key: $API_KEY" "$BASE_URL/activities/tree"

# Поиск организаций по названию
curl -H "X-API-Key: $API_KEY" "$BASE_URL/organizations/search/by-name?name=Рога"
```

## Полезные ссылки

После запуска доступны:
- **API Root**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Подробная документация

- `README.md` - Полное описание проекта
- `DEPLOYMENT.md` - Инструкции по развертыванию
- `API_EXAMPLES.md` - Примеры всех запросов
- `SUMMARY.md` - Сводка реализации
