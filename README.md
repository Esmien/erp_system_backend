![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python) ![Asyncio](https://img.shields.io/badge/Asyncio-Concurrency-blue?style=flat-square&logo=python) ![Pydantic](https://img.shields.io/badge/Pydantic-2.0+-blue?style=flat-square&logo=Pydantic) ![FastAPI](https://img.shields.io/badge/FastAPI-blue?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-orange?style=flat-square&logo=PostgreSQL) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM_v2.0+-orange?style=flat-square&logo=SQLAlchemy) ![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange?style=flat-square) ![Alembic](https://img.shields.io/badge/Adminer-Browse_DB-orange?style=flat-square&logo=adminer)
![Loguru](https://img.shields.io/badge/Loguru-Logging-brown?style=flat-square) ![Docker](https://img.shields.io/badge/Docker-Infrastructure-brown?style=flat-square&logo=docker) ![Redis](https://img.shields.io/badge/Redis-Infrastructure-brown?style=flat-square&logo=redis)

# Business Management Platform

**Проект представляет из себя RESTful-API для управления бизнесом.**

**Платформа предоставляет следующие возможности:**

1. Регистрацию/авторизацию пользователей (`JWT`)
2. RBAC/ABAC систему управления доступом к ресурсам по ролям и дополнительному контексту через политики доступа (`JSONB` в `PostgreSQL`)
3. Создание команд с инвайт-кодом для вступления пользователей в эти команды
4. Создание встреч с различными статусами этих встреч (назначена, в процессе, завершена/удалена)
5. Проверка расписания участников для предотвращения назначения нескольких встреч с пересечением по времени
6. Создание и управление задачами
7. Комментарии к задачам
8. Оценка завершенных задач
9. Сводная статистика по оценкам задач пользователей

---

Платформа написана по принципам `DDD` и `Clean Architecture` с разделением доменов и слоев (`Repository`-`Service`->`Transport`) и использованием паттерна Unit of Work для управления транзакциями.

Проект является самостоятельной разработкой уровня Production Ready с возможностью дальнейшей поддержки и расширения.
Написан по SOLID и позволяет расширять его без огромной когнитивной нагрузки. DDD-подход с использованием принципов чистой архитектуры позволяет быстро сориентироваться в проекте любому другому разработчику.
Интеграция новых фич не требует изучения полностью всех доменных сущностей, достаточно ознакомиться с ядром, которое написано очень логично и понятно

---

Возможности API представлены в документе [docs/API Features.md](docs/API%20Features.md)

---

### Быстрый запуск

---

1. #### Клонировать репозиторий:

```BASH
git clone https://github.com/Esmien/business_managment_platform.git bm_platform
```

---

2. #### Перейти в директорию проекта:

```BASH
cd bm_platform
```

---

3. #### Создать `.env`:

```BASH
cp .env.example .env
```

---

4. #### Сгенерировать секретный ключ, скопировать и вставить в .env в переменную **SECRET_KEY**:

```bash
openssl rand -base64 50
```

5. #### Изменить переменные окружения в `.env` на ваши (подробности в блоке `Конфигурация`)

---

6. #### Поднять контейнеры:

```BASH
docker compose up --build -d
```

---

### Конфигурация:

Конфигурация проекта реализована через `Pydantic-settings`, который берет данные из `.env`

Назначение каждой переменной кратко описано в `.env.example`

Если не заданы некоторые переменные окружения, 
будут взяты значения по умолчанию, прописанные в ```app/core/config.py```

---

*Интерактивная документация (Swagger UI) доступна после запуска контейнеров по адресу:*
*http://localhost:8000/docs*

---

### Тестовые данные (создаются автоматически)

1. **Администратор:**
* Email: `admin@admin.com`
* Password: `admin`

2. **Менеджер:**
* Email: `manager@manager.com`
* Password: `manager`

3. **Пользователь:**
* Email: `user@user.com`
* Password: `user`


**Роли по умолчанию:**
* `admin` (полные права)
* `manager` (частичные права к пользователям)
* `user` (права только на чтение своего профиля)

---

## Структура проекта:

```text
backend/
├── admin/                      # Управление админкой
│   ├── security.py             # Защита админки паролем, доступ только для админов
│   └── views.py                # Конфигурация интерфейса админки
├── api/                        # Транспортный слой (REST API)
│   ├── dependencies/           # Зависимости для DI в роутеры
│   ├── tests/                  # Тесты транспортного слоя
│   ├── v1/                     # Первая версия API
│   │   └── routers/            # Роутеры, разбитые по доменам
│   ├── exception_handlers.py   # Глобальный обработчик исключений для красивого вывода
│   └── main.py                 # Точка входа в приложение (FastAPI instance)
├── core/                       # Ядро и глобальная конфигурация
│   ├── database/               # Инфраструктура БД
│   │   ├── engine.py           # Движок SQLAlchemy и управление пулом соединений
│   │   └── init_db.py          # Скрипт наполнения базы стартовыми данными
│   ├── tests/                  # Тесты ядра (например, для Unit of Work)
│   ├── utils/                  # Общие утилиты и хелперы
│   ├── base_repository.py      # Базовый абстрактный репозиторий
│   ├── base_service.py         # Базовый абстрактный сервис
│   ├── config.py               # Настройки окружения (pydantic-settings)
│   ├── enums.py                # Глобальные перечисления (роли, статусы)
│   ├── logger.py               # Конфигурация Loguru
│   ├── policies.py             # Политики прав доступа (RBAC/ABAC)
│   ├── security.py             # Криптография (токены, хеширование паролей)
│   └── uow.py                  # Реализация паттерна Unit of Work
├── migrations/                 # Файлы миграций Alembic
├── task/                       # Пример доменного пакета (calendar, comment, meeting и др.)
│   ├── tests/                  # Тесты конкретного домена
│   ├── models.py               # ORM-модели SQLAlchemy
│   ├── repository.py           # Имплементация слоя доступа к данным
│   ├── schemas.py              # Pydantic-схемы валидации и сериализации
│   └── service.py              # Бизнес-логика домена
└── exceptions.py               # Базовые и кастомные доменные исключения
```


### Стек технологий:

---

| Категория      | Технологии                                 |
|----------------|--------------------------------------------|
| Backend        | `Python 3.12` `Asyncio` `FastAPI`          |
| Database       | `PostgreSQL` `SQLAlchemy 2.0` `Alembic`    |
| Infrastructure | `Docker` `Docker Compose` `Loguru` `Redis` |

---

### ToDo:

---

- [ ] Реализовать кэширование прав через Redis
- [ ] Реализовать инвалидацию JWT-токенов

Проект является самостоятельной разработкой уровня Production Ready с возможностью дальнейшей поддержки и расширения.
Написан по SOLID и позволяет расширять его без огромной когнитивной нагрузки. DDD-подход с использованием принципов чистой архитектуры позволяет быстро сориентироваться в проекте любому другому разработчику.
Интеграция новых фич не требует изучения полностью всех доменных сущностей, достаточно ознакомиться с ядром, которое написано очень логично и понятно