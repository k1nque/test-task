# API Examples

This file contains example requests for testing the Organizations Directory API.

## Environment Variables

```bash
export API_KEY="your-secret-api-key-change-in-production"
export BASE_URL="http://localhost:8000/api/v1"
```

## Organizations

### 1. Get All Organizations

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/organizations/?limit=10&offset=0"
```

### 2. Get Organization by ID

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/organizations/1"
```

### 3. Get Organizations by Building

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/organizations/by-building/1"
```

### 4. Get Organizations by Activity (with descendants)

```bash
# Get all organizations with activity "Еда" (Food) and its children
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/organizations/by-activity/1"
```

### 5. Search Organizations by Name

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/organizations/search/by-name?name=Рога"
```

### 6. Search Organizations by Radius

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": 55.7558,
    "longitude": 37.6173,
    "radius_meters": 5000,
    "limit": 10,
    "offset": 0
  }' \
  "$BASE_URL/organizations/search/by-location"
```

### 7. Search Organizations by Bounding Box

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
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
  "$BASE_URL/organizations/search/by-location"
```

### 8. Create New Organization

```bash
curl -X POST \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ООО \"Новая компания\"",
    "building_id": 1,
    "phone_numbers": [
      "8-800-555-00-00",
      "8-495-123-45-67"
    ],
    "activity_ids": [1, 2]
  }' \
  "$BASE_URL/organizations/"
```

## Buildings

### 1. Get All Buildings

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/buildings/?limit=10&offset=0"
```

### 2. Get Building by ID

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/buildings/1"
```

## Activities

### 1. Get All Activities (Flat List)

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/activities/?limit=50&offset=0"
```

### 2. Get Activities by Level

```bash
# Level 1 activities (root)
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/activities/?level=1"

# Level 2 activities
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/activities/?level=2"
```

### 3. Get Activity Tree

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/activities/tree"
```

### 4. Get Activity by ID (with children)

```bash
curl -H "X-API-Key: $API_KEY" \
  "$BASE_URL/activities/1"
```

## Health Check

```bash
curl http://localhost:8000/health
```

## Python Examples

### Using requests library

```python
import requests

API_KEY = "your-secret-api-key-change-in-production"
BASE_URL = "http://localhost:8000/api/v1"
headers = {"X-API-Key": API_KEY}

# Get all organizations
response = requests.get(f"{BASE_URL}/organizations/", headers=headers)
print(response.json())

# Search by location
search_data = {
    "latitude": 55.7558,
    "longitude": 37.6173,
    "radius_meters": 5000,
    "limit": 10,
    "offset": 0
}
response = requests.post(
    f"{BASE_URL}/organizations/search/by-location",
    headers=headers,
    json=search_data
)
print(response.json())

# Get activity tree
response = requests.get(f"{BASE_URL}/activities/tree", headers=headers)
print(response.json())

# Create new organization
new_org = {
    "name": "ООО \"Новая компания\"",
    "building_id": 1,
    "phone_numbers": ["8-800-555-00-00", "8-495-123-45-67"],
    "activity_ids": [1, 2]
}
response = requests.post(
    f"{BASE_URL}/organizations/",
    headers=headers,
    json=new_org
)
print(response.json())
```

## Test Data

The database is seeded with the following test data:

### Buildings
- ID 1: г. Москва, ул. Ленина 1, офис 3 (37.6173, 55.7558)
- ID 2: г. Москва, ул. Блюхера 32/1 (37.5850, 55.7344)
- ID 3: г. Новосибирск, пр. Красный 15 (82.9346, 55.0084)
- ID 4: г. Санкт-Петербург, Невский пр. 28 (30.3609, 59.9311)
- ID 5: г. Москва, ул. Арбат 10 (37.5951, 55.7520)

### Activities Tree
```
Еда (ID: 1)
├── Мясная продукция (ID: 2)
└── Молочная продукция (ID: 3)

Автомобили (ID: 4)
├── Грузовые (ID: 5)
└── Легковые (ID: 6)
    ├── Запчасти (ID: 7)
    └── Аксессуары (ID: 8)

Услуги (ID: 9)
└── Клининг (ID: 10)
```

### Organizations
1. ООО "Рога и Копыта" - Building 1, Activities: Мясная продукция, Молочная продукция
2. АО "Молочные реки" - Building 2, Activities: Молочная продукция, Еда
3. ИП Иванов "Мясная лавка" - Building 3, Activities: Мясная продукция, Еда
4. ООО "АвтоМир" - Building 4, Activities: Легковые, Запчасти, Аксессуары
5. ООО "ГрузАвто" - Building 2, Activities: Грузовые, Автомобили
6. ИП Петрова "Чистый дом" - Building 5, Activities: Клининг, Услуги
7. ООО "Продукты Сибири" - Building 3, Activities: Еда, Мясная продукция, Молочная продукция
8. ООО "Автозапчасти Плюс" - Building 5, Activities: Запчасти
