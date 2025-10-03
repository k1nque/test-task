# Тестирование эндпоинта создания организации

## Запуск приложения

```bash
# Запустите приложение
./start.sh

# Или
docker compose up -d
```

## Тестирование POST /api/v1/organizations/

### 1. Создание организации с curl

```bash
export API_KEY="your-secret-api-key-change-in-production"

curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ООО \"Тестовая компания\"",
    "building_id": 1,
    "phone_numbers": [
      "8-800-555-00-00",
      "8-495-123-45-67"
    ],
    "activity_ids": [1, 2]
  }' \
  http://localhost:8000/api/v1/organizations/ | jq
```

### 2. Проверка созданной организации

```bash
# Получить список всех организаций
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/organizations/ | jq

# Получить конкретную организацию (замените ID на полученный)
curl -H "X-API-Key: $API_KEY" \
  http://localhost:8000/api/v1/organizations/9 | jq
```

### 3. Тестирование валидации

#### Несуществующее здание (должно вернуть 404)

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест",
    "building_id": 999,
    "phone_numbers": ["123"],
    "activity_ids": [1]
  }' \
  http://localhost:8000/api/v1/organizations/
```

Ожидаемый ответ:
```json
{
  "detail": "Building with id 999 not found"
}
```

#### Несуществующая деятельность (должно вернуть 404)

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест",
    "building_id": 1,
    "phone_numbers": ["123"],
    "activity_ids": [999]
  }' \
  http://localhost:8000/api/v1/organizations/
```

Ожидаемый ответ:
```json
{
  "detail": "Activities with ids {999} not found"
}
```

#### Без API ключа (должно вернуть 403)

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тест",
    "building_id": 1,
    "phone_numbers": ["123"],
    "activity_ids": [1]
  }' \
  http://localhost:8000/api/v1/organizations/
```

## Тестирование через Swagger UI

1. Откройте http://localhost:8000/docs
2. Нажмите "Authorize" и введите API ключ
3. Найдите `POST /api/v1/organizations/`
4. Нажмите "Try it out"
5. Введите JSON:
   ```json
   {
     "name": "ООО \"Новая компания\"",
     "building_id": 1,
     "phone_numbers": [
       "8-800-555-00-00"
     ],
     "activity_ids": [1, 2]
   }
   ```
6. Нажмите "Execute"

## Тестирование с Python

```python
import requests

API_KEY = "your-secret-api-key-change-in-production"
BASE_URL = "http://localhost:8000/api/v1"
headers = {"X-API-Key": API_KEY}

# Создать организацию
new_org = {
    "name": "ООО \"Python Test\"",
    "building_id": 2,
    "phone_numbers": ["8-800-100-20-30", "8-495-999-88-77"],
    "activity_ids": [3, 4]
}

response = requests.post(
    f"{BASE_URL}/organizations/",
    headers=headers,
    json=new_org
)

if response.status_code == 201:
    org = response.json()
    print(f"✓ Организация создана! ID: {org['id']}")
    print(f"  Название: {org['name']}")
    print(f"  Телефоны: {[p['phone_number'] for p in org['phone_numbers']]}")
    print(f"  Деятельности: {[a['name'] for a in org['activities']]}")
else:
    print(f"✗ Ошибка {response.status_code}: {response.json()}")

# Проверить созданную организацию
org_id = org['id']
response = requests.get(
    f"{BASE_URL}/organizations/{org_id}",
    headers=headers
)
print(f"\n✓ Проверка: {response.json()['name']}")
```

## Ожидаемый результат

При успешном создании организации API должен вернуть:

```json
{
  "id": 9,
  "name": "ООО \"Тестовая компания\"",
  "building_id": 1,
  "phone_numbers": [
    {
      "phone_number": "8-800-555-00-00"
    },
    {
      "phone_number": "8-495-123-45-67"
    }
  ],
  "activities": [
    {
      "id": 1,
      "name": "Еда",
      "parent_id": null,
      "level": 1,
      "created_at": "...",
      "updated_at": "..."
    },
    {
      "id": 2,
      "name": "Мясная продукция",
      "parent_id": 1,
      "level": 2,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "building": {
    "id": 1,
    "address": "г. Москва, ул. Ленина 1, офис 3",
    "latitude": 55.7558,
    "longitude": 37.6173,
    "created_at": "...",
    "updated_at": "..."
  },
  "created_at": "...",
  "updated_at": "..."
}
```

Status code: `201 Created`
