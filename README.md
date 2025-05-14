# 🚀 Activity Joiner App

This is a FastAPI-based application with a PostgreSQL backend, set up for development using Docker Compose and tested with `pytest`.

---

## 💪 Running Tests

Before running the app, you can launch tests using `pytest`.

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

---

## ⚙️ Environment Setup

This project uses a `.env` file for environment variables.

### 1. Copy the example file:

```bash
cp .env.example .env
```

### 2. Edit `.env` with your actual credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<yourpassword>
DB_NAME=app_db
```

> Do **not** commit your `.env` file — it’s ignored by Git.

---

## 🐳 Running the App with Docker Compose

Make sure Docker and Docker Compose are installed, then launch the stack with:

```bash
docker-compose up --build web
```

This will:

* Start a PostgreSQL container (`db`)
* Build and start your FastAPI app (`web`)
* Wait for the database to be ready
* Run Alembic migrations
* Launch FastAPI on port `8000`

> PostgreSQL is exposed on port `5433` locally.

---

## 🔍 Access the API Docs

Once running, open your browser and navigate to:

```
http://localhost:8000/docs
```

This opens the **interactive Swagger UI** where you can test endpoints directly.

---

## 📌 Notes

* Alembic migrations are run automatically at container startup.
* Your application code is mounted into the Docker container (`volumes: .:/code`), so local changes reflect immediately.
* If you add new environment variables, remember to update `.env.example`.

---

## 🧹 Cleaning Up

To stop and remove containers, volumes, and networks:

```bash
docker-compose down -v
```

---
