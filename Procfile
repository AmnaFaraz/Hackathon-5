web: uvicorn production.api.main:app --host 0.0.0.0 --port $PORT
worker: python -m production.workers.message_processor
