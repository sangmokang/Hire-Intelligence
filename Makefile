.PHONY: dev build test migrate seed lint clean

# Development
dev:
	@echo "Starting development servers..."
	@make -j2 dev-fe dev-be

dev-fe:
	cd vxmi-dashboard && npm run dev

dev-be:
	cd backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000

# Docker
docker-dev:
	docker compose up --build

# Build
build-fe:
	cd vxmi-dashboard && npm run build

build-be:
	cd backend && docker build -t vxmi-api .

build: build-fe build-be

# Test
test-fe:
	cd vxmi-dashboard && npx tsc --noEmit

test-be:
	cd backend && source .venv/bin/activate && pytest

test-e2e:
	cd vxmi-dashboard && npx playwright test

test: test-fe test-be

# Database
migrate:
	cd backend && source .venv/bin/activate && alembic upgrade head

migrate-down:
	cd backend && source .venv/bin/activate && alembic downgrade -1

seed:
	cd backend && source .venv/bin/activate && python -m app.seed.apply_seed

# Lint
lint-fe:
	cd vxmi-dashboard && npm run lint

lint: lint-fe

# Clean
clean:
	rm -rf vxmi-dashboard/dist
	rm -rf backend/__pycache__
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
