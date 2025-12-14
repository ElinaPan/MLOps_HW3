# ML Model Deployment with Blue-Green and Canary Strategies (CI/CD)

Проект выполнен в рамках модуля **«Автоматизированное развертывание с помощью CI/CD»**.  
Цель проекта — продемонстрировать безопасное развертывание ML-моделей с использованием
стратегий **Blue-Green** и **Canary Deployment**, а также базовую автоматизацию деплоя
через **Docker** и **GitHub Actions**.


## Цели проекта

- Упаковка ML-модели в Docker-контейнер
- Реализация REST API для инференса модели
- Использование стратегий Blue-Green и Canary Deployment
- Переключение трафика и rollback при ошибках
- Проверка стабильности через эндпоинт `/health`
- Подготовка CI/CD workflow (GitHub Actions)


## Структура проекта


HW3/
├── app/
│   ├── model.pkl
│   └── requirements.txt
│
├── docker-compose.blue.yml
├── docker-compose.green.yml
├── docker-compose.nginx.yml
├── nginx.conf
├── Dockerfile
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
└── README.md




## ML-сервис

Используется предварительно обученная модель `model.pkl`.  
Сервис реализован с помощью **FastAPI** и предоставляет два эндпоинта:

### `/health`
Возвращает статус сервиса и версию модели:
```json
{
  "status": "ok",
  "version": "v1.0.0"
}
````

### `/predict`

Выполняет инференс модели:

```json
POST /predict
{
  "x": [1, 2, 3]
}
```

Ответ:

```json
{
  "prediction": [1],
  "model_version": "v1.0.0"
}
```

Версия модели передаётся через переменную окружения `MODEL_VERSION`.

## Docker

### Dockerfile

Контейнер собирается на основе минимального образа `python:3.11-slim`.

Основные шаги:

* установка зависимостей из `requirements.txt`
* копирование приложения
* запуск сервиса через `uvicorn`

---

## Blue-Green Deployment

Для Blue-Green деплоя используются два compose-файла:

* `docker-compose.blue.yml` — версия модели **v1.0.0**
* `docker-compose.green.yml` — версия модели **v1.1.0**

Обе версии сервиса могут работать **одновременно**.

> Версия модели (`MODEL_VERSION`) задаётся явно в `docker-compose`, так как:
>
> * версия модели не является секретом;
> * в стратегии Blue-Green используются **разные модели**, работающие параллельно.
>   Требование указания `MODEL_VERSION` в GitHub Secrets рассматривается как опечатка задания.

---

## Балансировка трафика (Nginx)

Для маршрутизации трафика используется **Nginx** (`docker-compose.nginx.yml`).

### Blue-Green переключение

Переключение между версиями выполняется путём изменения upstream в `nginx.conf`
и перезапуска контейнера nginx.

### Canary Deployment (90/10 → 100%)

Пример конфигурации для Canary 90/10:

```nginx
upstream ml_backend {
    server mlservice_blue:8080 weight=9;
    server mlservice_green:8080 weight=1;
}
```

Постепенное увеличение доли новой версии:

* 90/10 → 50/50 → 100%
* rollback выполняется возвратом трафика на предыдущую версию



##  Локальный запуск (Windows / PowerShell)

### 1. Создание общей сети

```powershell
docker network create bgnet
```

### 2. Запуск blue и green сервисов

```powershell
docker compose -f docker-compose.blue.yml up -d --build
docker compose -f docker-compose.green.yml up -d --build
```

### 3. Запуск nginx

```powershell
docker compose -f docker-compose.nginx.yml up -d
```

---

## Проверка работоспособности

### Проверка напрямую

```powershell
curl http://localhost:8080/health | Select-Object -ExpandProperty Content
curl http://localhost:8081/health | Select-Object -ExpandProperty Content
```

### Проверка через балансировщик

```powershell
curl http://localhost:8086/health | Select-Object -ExpandProperty Content
```

---

## Проверка Canary-распределения (20 запросов)

```powershell
1..20 | ForEach-Object {
    (Invoke-WebRequest http://localhost:8086/health).Content | ConvertFrom-Json
} | Group-Object version | Select-Object Name, Count
```


## Rollback

Rollback выполняется мгновенно:

1. изменение upstream в `nginx.conf`
2. перезапуск nginx:

```powershell
docker compose -f docker-compose.nginx.yml restart nginx
```

---

## CI/CD (GitHub Actions)

В проекте настроен workflow `.github/workflows/deploy.yml`, который:

* собирает Docker-образ
* публикует его в контейнерный реестр
* выполняет деплой через API облачного провайдера

Используемые секреты GitHub:

* `CLOUD_TOKEN`


## Результат

* Реализованы стратегии **Blue-Green** и **Canary Deployment**
* Настроена балансировка и rollback
* Добавлен мониторинг через `/health`
* Проект полностью готов к автоматизированному деплою
