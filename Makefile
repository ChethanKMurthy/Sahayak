.PHONY: help install backend web mobile test smoke fmt lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

install: ## Install backend + web dependencies
	cd backend && python3.12 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd web && npm install

backend: ## Run the FastAPI backend with reload
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

web: ## Run the Next.js dev server
	cd web && npm run dev

mobile: ## Run the Flutter app
	cd mobile && flutter run

test: ## Run backend unit tests
	cd backend && . .venv/bin/activate && pytest -q tests

smoke: ## Run the end-to-end smoke test
	cd backend && . .venv/bin/activate && python smoke_test.py

fmt: ## Auto-format Python (black + ruff) and web (prettier)
	cd backend && . .venv/bin/activate && black app && ruff check --fix app
	cd web && npx prettier --write .

lint: ## Lint Python (ruff) and web (eslint)
	cd backend && . .venv/bin/activate && ruff check app
	cd web && npm run lint

clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf web/.next
