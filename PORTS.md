# Конфигурация портов

## Docker контейнеры

### PostgreSQL (db)
- **Внутренний порт**: 5432 (стандартный порт PostgreSQL внутри контейнера)
- **Внешний порт**: 5434 (проброшен наружу для избежания конфликта с локальным PostgreSQL)

**Почему разные порты?**
- Если на вашей машине уже запущен PostgreSQL на порту 5432, использование того же порта вызовет конфликт
- Внутри Docker сети контейнеры общаются по стандартным портам (5432)
- Снаружи мы можем подключиться через порт 5434

**Подключение:**

Из контейнера API:
```bash
# API контейнер использует имя хоста 'db' и порт 5432
POSTGRES_SERVER=db
POSTGRES_PORT=5432
```

Из хост-машины:
```bash
# Подключение через внешний порт 5434
psql -h localhost -p 5434 -U postgres -d organizations_db

# Или через параметры подключения
postgresql://postgres:postgres@localhost:5434/organizations_db
```

Через Docker exec (внутрь контейнера):
```bash
# Подключение внутри контейнера использует стандартный порт
docker compose exec db psql -U postgres -d organizations_db
```

### API сервис
- **Внутренний порт**: 8000 (FastAPI работает на этом порту)
- **Внешний порт**: 8000 (проброшен 1:1)

**Доступ:**
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Изменение портов

Если вам нужно изменить внешние порты, отредактируйте `docker-compose.yml`:

```yaml
services:
  db:
    ports:
      - "ВНЕШНИЙ_ПОРТ:5432"  # Например: "15432:5432"
  
  api:
    ports:
      - "ВНЕШНИЙ_ПОРТ:8000"  # Например: "8080:8000"
```

**Важно:** Меняйте только первое число (внешний порт), второе число должно оставаться как есть!

## Проверка портов

Проверить какие порты слушает Docker:
```bash
docker compose ps
```

Проверить занятые порты на хосте:
```bash
# Linux/macOS
sudo lsof -i :5432
sudo lsof -i :5434
sudo lsof -i :8000

# Или
netstat -tulpn | grep -E '5432|5434|8000'
```

## Troubleshooting

### Порт 5434 тоже занят?

Измените внешний порт в docker-compose.yml:
```yaml
services:
  db:
    ports:
      - "15432:5432"  # Используйте любой свободный порт
```

Затем подключайтесь через новый порт:
```bash
psql -h localhost -p 15432 -U postgres -d organizations_db
```

### Ошибка "port is already allocated"

Это означает, что внешний порт занят другим процессом. Варианты решения:

1. Остановите другой сервис, использующий этот порт
2. Измените внешний порт в docker-compose.yml
3. Используйте `docker compose down -v` для полной очистки и перезапустите

### Контейнер запущен, но не отвечает

Проверьте логи:
```bash
docker compose logs db
docker compose logs api
```

Проверьте health check:
```bash
docker compose ps
# Статус должен быть "healthy" для db
```
