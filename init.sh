#!/bin/bash
# init.sh — Future Engine startup script
# Rodar no início de cada sessão de desenvolvimento
# Garante ambiente limpo e testável

set -e

echo "=== Future Engine — Init ==="

# 1. Verificar dependências
echo "[1/5] Verificando dependências..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker não encontrado. Instale Docker antes de continuar."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 não encontrado."; exit 1; }

# 2. Verificar .env
echo "[2/5] Verificando .env..."
if [ ! -f ".env" ]; then
  echo "⚠️  .env não encontrado. Copiando .env.example..."
  cp .env.example .env
  echo "✅ .env criado. Revise as configurações antes de continuar."
fi

# Confirmar que modo real está desligado
LIVE=$(grep "LIVE_TRADING_ENABLED" .env | cut -d= -f2 | tr -d ' ')
if [ "$LIVE" = "true" ]; then
  echo "⚠️  ATENÇÃO: LIVE_TRADING_ENABLED=true detectado."
  read -p "Confirmar que deseja operar em modo real? (yes/no): " confirm
  if [ "$confirm" != "yes" ]; then
    echo "❌ Abortado. Edite .env para continuar."
    exit 1
  fi
else
  echo "✅ Modo paper confirmado (LIVE_TRADING_ENABLED=false)"
fi

# 3. Subir containers (com fallback local se Docker Hub inacessível)
echo "[3/5] Subindo containers..."
USE_LOCAL=false

# Carregar variáveis do .env para uso no fallback local
set -a; source .env; set +a

# Verificar se API já está respondendo (sessão já inicializada)
if curl -s http://localhost:8000/health | grep -q '"status":"ok"' 2>/dev/null; then
  echo "✅ API já está em execução."
else
  # Tentar docker compose; capturar saída sem propagar sinal de kill
  DOCKER_OUT=$(docker compose up -d --build 2>&1) && DOCKER_EXIT=0 || DOCKER_EXIT=$?
  if [ "$DOCKER_EXIT" -eq 0 ]; then
    echo "$DOCKER_OUT"
    sleep 3
  else
    echo "$DOCKER_OUT" | tail -5
    echo "⚠️  Docker build falhou (sem acesso ao Docker Hub?). Usando modo local com uvicorn."
    USE_LOCAL=true
    # Garantir dependências Python instaladas
    pip install -q fastapi "uvicorn[standard]" pydantic 2>/dev/null || true
    # Garantir diretório do banco de dados
    DB_DIR=$(dirname "${DB_PATH:-/tmp/future_engine.db}")
    mkdir -p "$DB_DIR" 2>/dev/null || export DB_PATH="/tmp/future_engine.db"
    # Matar API anterior se existir
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    sleep 1
    # Subir API em background
    PYTHONPATH="$(pwd)" uvicorn app.main:app --host 0.0.0.0 --port 8000 &>/tmp/future_engine_api.log &
    sleep 3
  fi
fi

# 4. Health check
echo "[4/5] Verificando saúde da API..."
MAX_RETRIES=10
RETRY=0
until curl -s http://localhost:8000/health | grep -q '"status":"ok"' 2>/dev/null; do
  RETRY=$((RETRY+1))
  if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "❌ API não respondeu após ${MAX_RETRIES} tentativas."
    if [ "$USE_LOCAL" = "true" ]; then
      echo "Logs da API local:"
      tail -20 /tmp/future_engine_api.log 2>/dev/null
    else
      echo "Logs:"
      docker compose logs api --tail=20
    fi
    exit 1
  fi
  echo "   Aguardando API... ($RETRY/$MAX_RETRIES)"
  sleep 2
done
echo "✅ API respondendo em http://localhost:8000"
echo "✅ UI disponível em http://localhost:8501"
echo "✅ Swagger em http://localhost:8000/docs"

# 5. Smoke test rápido
echo "[5/5] Rodando smoke test..."
SIGNAL_RESP=$(curl -s -X POST http://localhost:8000/signals/generate \
  -H "Content-Type: application/json" \
  -d '{"symbols":["BTCUSDT"],"timeframe":"4h"}')

if echo "$SIGNAL_RESP" | grep -q '"signals"'; then
  echo "✅ Smoke test passou — geração de sinais funcionando"
else
  echo "❌ Smoke test falhou. Response:"
  echo "$SIGNAL_RESP"
  exit 1
fi

echo ""
echo "=== Ambiente pronto ==="
echo ""
echo "Próximo passo recomendado:"
echo "  1. Leia harness/claude-progress.txt para entender o estado atual"
echo "  2. Leia harness/feature_list.json para ver features pendentes"
echo "  3. Escolha a próxima feature e trabalhe uma de cada vez"
echo ""
