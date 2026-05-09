# docs/comandos.md — Comandos de referencia TributarioPY

## Entorno virtual

| Comando | Descripción |
|---|---|
| `python -m venv venv` | Crea el entorno virtual |
| `source venv/bin/activate` | Activa (Linux/Mac) |
| `venv\Scripts\activate` | Activa (Windows) |
| `deactivate` | Desactiva |

## Dependencias

| Comando | Descripción |
|---|---|
| `pip install -r requirements.txt` | Instala dependencias |
| `pip freeze > requirements.txt` | Regenera requirements |

## Servidor

| Comando | Descripción |
|---|---|
| `uvicorn app.main:app --reload` | FastAPI con recarga automática |
| `uvicorn app.main:app --reload --host 0.0.0.0` | Accesible desde otros dispositivos en la red local |

## Docker (PostgreSQL)

| Comando | Descripción |
|---|---|
| `docker compose up -d` | Levanta PostgreSQL |
| `docker compose down` | Detiene PostgreSQL |
| `docker ps` | Lista contenedores corriendo |

## PostgreSQL directo

| Comando | Descripción |
|---|---|
| `docker exec -it tributario-db psql -U admin -d tributario_py -c "\dt"` | Lista tablas |
| `docker exec -it tributario-db psql -U admin -d tributario_py` | Consola interactiva |

## Alembic

| Comando | Descripción |
|---|---|
| `alembic revision --autogenerate -m "descripcion"` | Genera migración |
| `alembic upgrade head` | Aplica migraciones pendientes |
| `alembic downgrade -1` | Revierte la última migración |
| `alembic current` | Migración actualmente aplicada |
| `alembic history` | Lista todas las migraciones |

## Seed

| Comando | Descripción |
|---|---|
| `python -m app.seed.run` | Ejecuta seed data (categorías, reglas, config fiscal) |

## Frontend (cuando se implemente)

| Comando | Descripción |
|---|---|
| `cd frontend && npm install` | Instala dependencias del frontend |
| `cd frontend && npm run dev` | Vite dev server |
| `cd frontend && npm run build` | Build de producción |
