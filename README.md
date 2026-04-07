# Двухсервисная система LLM-консультаций

# Описание проекта

Проект представляет собой распределённую систему, состоящую из двух логически и технически независимых сервисов:

1. **Auth Service** - сервис аутентификации и выдачи JWT-токенов
2. **Bot Service** - Telegram-бот для консультаций с LLM через OpenRouter

Архитектура построена по принципу разделения ответственности: Auth Service отвечает за управление пользователями и выпуск токенов, Bot Service доверяет только валидным JWT-токенам и не хранит пользовательские данные.

# Auth Service 

Auth Service отвечает исключительно за управление пользователями и выпуск JWT-токенов и может быть использован любыми внешними клиентами без привязки к Telegram-боту.

Swagger UI доступен по адресу http://localhost:8000/docs.

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/auth/register` | POST | Регистрация нового пользователя |
| `/auth/login` | POST | Аутентификация и получение JWT |
| `/auth/me` | GET | Получение профиля текущего пользователя |
| `/health` | GET | Проверка работоспособности |

- Пароли хранятся только в виде хешей (`bcrypt`)
- JWT содержит поля: `sub` (id пользователя), `role`, `iat`, `exp`
- Валидация входных данных через Pydantic
- ORM: `SQLAlchemy` (асинхронная работа с SQLite через `aiosqlite`)
- Кастомные исключения для всех HTTP ошибок

# Bot Service 

Сервис предоставляет Telegram-бота для общения с LLM через OpenRouter. Bot Service не содержит логики регистрации и входа, не хранит пользователей и не обращается напрямую к базе Auth Service, а доверяет только корректно подписанному и не истёкшему JWT.

| Команда | Описание |
|---------|----------|
| `/start` | Приветственное сообщение с инструкцией по использованию |
| `/token <JWT>` | Сохранение JWT токена в Redis (токен привязывается к `user_id`) |
| Любой текст | Отправка запроса к LLM (требуется предварительное сохранение валидного токена) |

- Telegram Bot (`aiogram`) — приём входящих сообщений от пользователей через polling, валидация JWT токенов (проверка подписи, срока действия, наличия `sub`)
- Celery Worker — асинхронная обработка задач из очереди RabbitMQ, вызов OpenRouter API, отправка ответов пользователям через Telegram Bot API, автоматические повторы при ошибках
- RabbitMQ — брокер сообщений, очередь задач между Telegram Bot и Celery Worker, подтверждение выполнения задач
- Redis — хранение JWT токенов, привязанных к Telegram `user_id` (ключи вида `token:{user_id}`, TTL 1 час)

### **Bot API (FastAPI)**

Вспомогательный HTTP-сервер для мониторинга работоспособности (`GET /health`) по ссылке http://localhost:8001/health

<img width="326" height="113" alt="Снимок экрана 2026-04-07 в 02 00 54" src="https://github.com/user-attachments/assets/8dd96b10-b7a0-4d56-b0be-2b0fbb134c39" />

# Сценарий работы 

1. **Регистрация** — пользователь отправляет `POST /auth/register` через Swagger UI (`http://localhost:8000/docs`), указывая email и пароль.

2. **Получение токена** — пользователь отправляет `POST /auth/login` с данными `username` (email) и `password`; при успешной аутентификации Auth Service возвращает JWT-токен.

3. **Запуск бота** — пользователь отправляет боту команду `/start`; бот приветствует и описывает порядок работы.

4. **Сохранение токена** — пользователь отправляет боту команду `/token <JWT>`; бот валидирует подпись и срок действия токена, при успехе сохраняет его в Redis.

5. **Отправка запроса** — пользователь отправляет боту текстовый вопрос; бот проверяет наличие и валидность JWT в Redis, публикует задачу `llm_request` в RabbitMQ.

6. **Подтверждение** — бот отвечает пользователю: «Запрос принят в обработку. Ответ придёт следующим сообщением».

7. **Обработка** — Celery worker забирает задачу из очереди, отправляет запрос к OpenRouter API.

8. **Ответ** — Celery worker получает ответ от LLM и отправляет его пользователю через Telegram Bot API.

Если токен отсутствует, невалиден или истёк, бот отказывает в доступе и предлагает авторизоваться через Auth Service.

# Запуск проекта

### 1. Подготовка

Перед запуском проекта необходимо получить следующие токены:

- Telegram Bot Token [@BotFather](https://t.me/BotFather) 
- OpenRouter API Key [OpenRouter](https://openrouter.ai/)

### 2. Настройка переменных окружения

- Auth Service (`auth_service/.env`)

Скопируйте файл примера и отредактируйте `JWT_SECRET`

```bash
cd auth_service
cp .env.example .env
```

- Bot Service (`bot_service/.env`)

Скопируйте файл примера и отредактируйте следующие параметры: `TELEGRAM_BOT_TOKEN`, `JWT_SECRET`, `OPENROUTER_API_KEY`

```bash
cd bot_service
cp .env.example .env
```

**Важно:** `JWT_SECRET` должен быть ОДИНАКОВЫМ в обоих сервисах!

### 3. Запуск через Docker Compose

Из корневой директории проекта выполните:

```bash
docker compose up --build
```

После запуска будут доступны:

| Сервис | URL |
|--------|-----|
| Auth Service (Swagger UI) | http://localhost:8000/docs |
| RabbitMQ Management | http://localhost:15672 (guest / guest) |
| Bot API Health | http://localhost:8001/health |

**Telegram Bot**: После запуска найдите вашего бота в Telegram по username, который вы указали при создании через `@BotFather`

### 4. Остановка

```bash
docker compose down
```

# Демонстрация работы

### 1. Swagger Auth Service

- Регистрация пользователя (`POST /auth/register`)

<img width="724" height="703" alt="Снимок экрана 2026-04-07 в 15 41 50" src="https://github.com/user-attachments/assets/533130a4-517e-4879-b14a-51b4e9e188b1" />

- Логин и получение токена (`POST /auth/login`)

<img width="726" height="749" alt="Снимок экрана 2026-04-07 в 15 50 38" src="https://github.com/user-attachments/assets/4ebee5fd-8ec8-487f-999a-531e9973b556" />

- Авторизация в Swagger UI
  
<img width="481" height="438" alt="Снимок экрана 2026-04-07 в 15 46 22" src="https://github.com/user-attachments/assets/7fd35d5f-3e4d-4a63-9067-4c4550c990dc" />

<img width="447" height="322" alt="Снимок экрана 2026-04-07 в 15 46 46" src="https://github.com/user-attachments/assets/41932347-7044-4a92-84e0-65426d704c9f" />

- Получение профиля по токену (`GET /auth/me`)

<img width="1063" height="663" alt="Снимок экрана 2026-04-07 в 15 47 26" src="https://github.com/user-attachments/assets/e806cfe7-0260-4c8e-b366-62d1ef6ba359" />

- Проверка работоспособности (`GET /health`)

<img width="1071" height="662" alt="Снимок экрана 2026-04-07 в 15 49 55" src="https://github.com/user-attachments/assets/cf84780d-169d-422c-b84a-2ecb15cfc345" />

### 2. Telegram Bot

- Команда `/start`

<img width="588" height="469" alt="Снимок экрана 2026-04-07 в 15 52 17" src="https://github.com/user-attachments/assets/adae3449-235a-4cf0-84c0-e11e6664a61b" />

- Сохранение JWT токена (`/token`)

<img width="544" height="257" alt="Снимок экрана 2026-04-07 в 16 26 52" src="https://github.com/user-attachments/assets/fc3c9445-5869-4e5f-a7bb-c81034c04d9f" />

- Запрос к LLM и ответ

<img width="568" height="784" alt="Снимок экрана 2026-04-07 в 16 45 35" src="https://github.com/user-attachments/assets/3b5098c4-2583-4184-82f3-c45b5251561d" />

### 3. RabbitMQ

<img width="1389" height="724" alt="Снимок экрана 2026-04-07 в 16 50 00" src="https://github.com/user-attachments/assets/ec8770d4-1719-48f0-85c9-09f40a4166ce" />

# Тестирование

Тесты разделены на модульные, интеграционные и мок-тесты. Все тесты проходят локально без Docker и внешних сервисов (используются `fakeredis`, `respx`, `pytest-mock`, `ASGITransport`, `in-memory SQLite`).

### Auth Service тесты

| Тип тестов | Файлы | Что проверяют |
|------------|-------|---------------|
| Модульные | `test_security.py` | Хеширование паролей (bcrypt), генерация и валидация JWT (`sub`, `role`, `iat`, `exp`) |
| Модульные | `test_repositories.py` | CRUD операции: `create`, `get_by_email`, `get_by_id` |
| Модульные | `test_usecases.py` | Бизнес-логику: регистрация, логин, получение профиля |
| Интеграционные | `test_api.py` | HTTP эндпоинты (201, 200, 401, 409, 422) через `ASGITransport` + `in-memory SQLite` |

Для запуска тестов выполните в терминале:

```
cd auth_service
pytest tests/ -v
```

<img width="1047" height="650" alt="Снимок экрана 2026-04-07 в 02 56 20" src="https://github.com/user-attachments/assets/5e05feb5-cf73-43ea-a320-133bfe297501" />

### Bot Service тесты

| Тип тестов | Файлы | Что проверяют |
|------------|-------|---------------|
| Модульные | `test_jwt.py` | Валидацию JWT (валидный, невалидный, истекший, пустой, битый токен) |
| Мок-тесты | `test_handlers.py` | Команды бота: `/start`, `/token`, текст без токена, текст с токеном, истекший токен (с `fakeredis`) |
| Интеграционные | `test_openrouter.py` | HTTP клиент к OpenRouter API (успех, ошибки, payload, headers) через `respx` |

Для запуска тестов выполните в терминале:

```
cd bot_service
pytest tests/ -v
```

<img width="1146" height="425" alt="Снимок экрана 2026-04-07 в 02 57 01" src="https://github.com/user-attachments/assets/2a296558-c3f5-4798-aedf-2c6033fa0e80" />

# Линтер 

Для проверки качества кода используется `ruff`. Запуск проверки осуществляется из корневой директории проекта:

```
uv run ruff check
```
<img width="641" height="32" alt="Снимок экрана 2026-04-07 в 15 21 11" src="https://github.com/user-attachments/assets/8f0d2802-2b1e-4928-a7b6-f11b63bce8c5" />
