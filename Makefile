.PHONY: dev dev-db dev-backend dev-frontend stop test lint migrate build deploy clean

# ===== One command to rule them all =====
dev: dev-db
	@echo "⏳ Waiting for Postgres..."
	@sleep 3
	@make dev-backend &
	@sleep 2
	@make dev-frontend

# ===== Individual services =====
dev-db:
	docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Database running on port 5433"

dev-backend:
	cd backend && uvicorn app:app --reload --port 5001

dev-frontend:
	cd frontend && npm run dev

# ===== Stop everything =====
stop:
	docker-compose -f docker-compose.dev.yml down
	@pkill -f "uvicorn app:app" 2>/dev/null || true
	@echo "✅ All services stopped"

# ===== Testing =====
test:
	cd backend && pytest tests/ -v

lint:
	cd backend && pip install ruff && ruff check . --select F --ignore F401,F841

# ===== Database =====
migrate:
	cd backend && alembic upgrade head

migrate-new:
	@read -p "Migration name: " name; \
	cd backend && alembic revision --autogenerate -m "$$name"

# ===== Build =====
build:
	docker-compose build

# ===== Production (full stack Docker) =====
prod:
	docker-compose up --build -d
	@echo "✅ Production stack running on http://localhost"

prod-down:
	docker-compose down

# ===== Deploy =====
deploy-azure:
	chmod +x deploy-azure.sh && ./deploy-azure.sh

# ===== Clean =====
clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose down -v
	rm -rf backend/__pycache__ backend/**/__pycache__ backend/.pytest_cache
	rm -rf frontend/node_modules frontend/dist
	@echo "✅ Cleaned"

# ===== Setup (first time) =====
setup:
	@echo "📦 Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "🐳 Starting database..."
	docker-compose -f docker-compose.dev.yml up -d
	@sleep 3
	@echo "🗄️  Running migrations..."
	cd backend && alembic upgrade head
	@echo ""
	@echo "✅ Setup complete! Run 'make dev' to start developing."
