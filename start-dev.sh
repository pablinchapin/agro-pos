#!/bin/bash

# =============================================================================
# Agro POS — Dev Environment Startup Script
# Run from project root: ./start-dev.sh
# =============================================================================

set -e  # exit on first error

echo "🌱 Starting Agro POS dev environment..."
echo ""

# Load environment variables
if [ ! -f .env ]; then
  echo "❌ .env file not found. Copy .env.example to .env and fill in your values."
  exit 1
fi

source .env

# -----------------------------------------------------------------------------
# 1. Check required tools
# -----------------------------------------------------------------------------
# PVM for tool in kubectl psql python3; do
for tool in kubectl python3; do
  if ! command -v $tool &> /dev/null; then
    echo "❌ Required tool not found: $tool"
    exit 1
  fi
done
echo "✅ Required tools found"

# -----------------------------------------------------------------------------
# 2. Start Kubernetes port-forward for PostgreSQL
# -----------------------------------------------------------------------------
echo "📡 Starting PostgreSQL port-forward..."

# Kill any existing port-forward on 5432
pkill -f "kubectl port-forward.*5432" 2>/dev/null || true
sleep 1

kubectl port-forward svc/$K8S_POSTGRES_SERVICE 5432:5432 -n $K8S_NAMESPACE > /tmp/kubectl-pf.log 2>&1 &
PF_PID=$!
echo "   Port-forward PID: $PF_PID"

# Wait for port-forward to be ready
echo "   Waiting for port-forward to stabilize..."
sleep 3


# -----------------------------------------------------------------------------
# 3. Activate virtual environment
# -----------------------------------------------------------------------------
echo "🐍 Activating virtual environment..."

if [ ! -f .venv/bin/activate ]; then
  echo "❌ Virtual environment not found. Run: python3 -m venv .venv && pip install -r backend/requirements.txt"
  exit 1
fi

source .venv/bin/activate
echo "✅ Virtual environment active ($(python3 --version))"


# -----------------------------------------------------------------------------
# 4. Verify PostgreSQL connection
# -----------------------------------------------------------------------------
# echo "🐘 Verifying PostgreSQL connection..."

# if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\q" 2>/dev/null; then
#   echo "✅ PostgreSQL connected ($DB_HOST:$DB_PORT/$DB_NAME)"
# else
#   echo "❌ PostgreSQL connection failed."
#   echo "   Check your .env credentials and that the pod is running:"
#   echo "   kubectl get pods -n $K8S_NAMESPACE"
#   kill $PF_PID 2>/dev/null || true
#   exit 1
# fi

echo "🐘 Verifying PostgreSQL connection..."
MAX_RETRIES=5
RETRY=0
until python3 -c "
import asyncio, sys
async def check():
    import asyncpg
    conn = await asyncpg.connect(
        host='$DB_HOST', port=$DB_PORT,
        user='$DB_USER', password='$DB_PASSWORD',
        database='$DB_NAME'
    )
    await conn.close()
asyncio.run(check())
" 2>/dev/null; do
  RETRY=$((RETRY+1))
  if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "❌ PostgreSQL connection failed after $MAX_RETRIES attempts."
    echo "   Check your .env credentials and that the pod is running:"
    echo "   kubectl get pods -n $K8S_NAMESPACE"
    kill $PF_PID 2>/dev/null || true
    exit 1
  fi
  echo "   Retrying ($RETRY/$MAX_RETRIES)..."
  sleep 2
done
echo "✅ PostgreSQL connected ($DB_HOST:$DB_PORT/$DB_NAME)"



# -----------------------------------------------------------------------------
# 5. Apply pending migrations
# -----------------------------------------------------------------------------
echo "🗃️  Applying pending Alembic migrations..."
cd backend
alembic upgrade head
cd ..
echo "✅ Migrations up to date"

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "✅ Agro POS dev environment ready."
echo ""
echo "   Run each in a separate terminal:"
echo "   Backend:    source .venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000"
echo "   Frontend:   source .venv/bin/activate && cd frontend && streamlit run app.py"
echo "   Claude Code: claude"
echo ""
echo "   Port-forward running in background (PID: $PF_PID)"
echo "   To stop it: kill $PF_PID"
echo "   Or:         pkill -f 'kubectl port-forward.*5432'"