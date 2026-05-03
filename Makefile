.PHONY: setup setup-backend setup-frontend backend frontend dev

setup-backend:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements.txt

setup-frontend:
	npm --prefix frontend install

setup: setup-backend setup-frontend

backend:
	cd backend && ../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev -- --host 127.0.0.1 --port 5173

dev:
	./scripts/dev.sh
