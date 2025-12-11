# Руководство по работе с Car Inventory API

## Запуск проекта

1. Убедитесь, что у вас установлен Docker и Docker Compose
2. В корневой директории проекта выполните:
```bash
docker-compose up -d
```
3. Приложение будет доступно по адресу `http://localhost:5001`

## Основные команды Docker Compose

- Запуск проекта: `docker-compose up -d`
- Остановка проекта: `docker-compose down`
- Просмотр статуса контейнеров: `docker-compose ps`
- Просмотр логов веб-приложения: `docker-compose logs web`
- Просмотр логов воркера: `docker-compose logs worker`

## API endpoints

### Получить информацию о API
```
GET http://localhost:5001/
```

### Получить все автомобили
```
GET http://localhost:5001/cars
```

### Получить автомобиль по ID
```
GET http://localhost:5001/cars/{id}
```

### Создать новый автомобиль
```
POST http://localhost:5001/cars
Content-Type: application/json

{
  "make": "Toyota",
  "model": "Camry",
  "year": 2020
}
```

### Обновить автомобиль
```
PUT http://localhost:5001/cars/{id}
Content-Type: application/json

{
  "make": "Toyota",
  "model": "Camry",
  "year": 2021
}
```

### Удалить автомобиль
```
DELETE http://localhost:5001/cars/{id}
```

### Получить статистику запросов
```
GET http://localhost:5001/stats
```

### Проверка состояния сервисов
```
GET http://localhost:5001/health
```

## Примеры использования

### Создание автомобиля
```bash
curl -X POST http://localhost:5001/cars \
  -H "Content-Type: application/json" \
  -d '{"make": "Honda", "model": "Civic", "year": 2019}'
```

### Получение всех автомобилей
```bash
curl http://localhost:5001/cars
```

### Получение автомобиля по ID
В URL нужно указать конкретный ID автомобиля:
```
http://localhost:5001/cars/1
```

### Обновление автомобиля
В URL нужно указать конкретный ID автомобиля:
```
http://localhost:5001/cars/1
```

Пример с curl:
```bash
curl -X PUT http://localhost:5001/cars/1 \
  -H "Content-Type: application/json" \
  -d '{"year": 2022}'
```

### Удаление автомобиля
В URL нужно указать конкретный ID автомобиля:
```
http://localhost:5001/cars/1
```

Пример с curl:
```bash
curl -X DELETE http://localhost:5001/cars/1
```

## Архитектура

Проект состоит из следующих компонентов:

1. **Веб-приложение (Flask)** - обрабатывает HTTP-запросы и взаимодействует с базой данных
2. **PostgreSQL** - основная база данных для хранения информации об автомобилях
3. **Redis** - используется для кэширования данных для ускорения чтения
4. **Kafka** - шина сообщений для асинхронной обработки событий
5. **Worker** - обрабатывает события из Kafka и выполняет бизнес-логику

## События Kafka

При выполнении операций с автомобилями генерируются следующие события:
- `car_created` - при создании автомобиля
- `car_updated` - при обновлении автомобиля
- `car_deleted` - при удалении автомобиля

## Логирование

- Логи веб-приложения: `docker-compose logs web`
- Логи воркера: `docker-compose logs worker`

## Остановка проекта

Для остановки всех сервисов выполните:
```bash
docker-compose down
```

## Устранение неполадок

1. Если порт 5001 занят, измените его в файле `docker-compose.yml`
2. Если возникают проблемы с запуском Kafka, проверьте логи: `docker-compose logs kafka`
3. Для перезапуска отдельного сервиса: `docker-compose restart web`