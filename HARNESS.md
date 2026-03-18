# Future Engine — Harness Architecture

Este documento é a fonte de verdade para qualquer agente ou desenvolvedor que trabalhe no projeto.

---

## O que é o harness

O harness é o ambiente completo no qual o agente opera. Não é o código da aplicação — é o conjunto de scaffolding que permite que o código da aplicação seja desenvolvido de forma coerente, incremental e recuperável.

```
harness/
  feature_list.json      → o que "pronto" significa (âncora cognitiva)
  claude-progress.txt    → memória cross-session

prompts/
  initializer_prompt.md  → prompt da sessão de setup
  coding_agent_prompt.md → prompt de todas as sessões de desenvolvimento

init.sh                  → startup reproduzível
HARNESS.md               → este documento
```

---

## Como funciona o ciclo de desenvolvimento

```
┌─────────────────────────────────────────────┐
│  Sessão de Inicialização (roda uma vez)     │
│  → Auditoria do código existente            │
│  → feature_list.json com estado real        │
│  → claude-progress.txt criado               │
│  → init.sh funcionando                      │
│  → git commit inicial                       │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Sessão de Desenvolvimento (repete)         │
│  1. Startup sequence (5 passos)             │
│  2. Ler feature_list — escolher 1 feature   │
│  3. Implementar                             │
│  4. Verificar end-to-end                    │
│  5. Atualizar feature_list + progress       │
│  6. Git commit com mensagem descritiva      │
└──────────────┬──────────────────────────────┘
               │
               ▼
         (próxima sessão)
```

---

## Regras invioláveis

1. **Uma feature por sessão** — completar antes de começar outra
2. **Verificação end-to-end obrigatória** — não marcar passes:true só por unit test
3. **Estado limpo obrigatório** — nunca commitar código que quebra testes existentes
4. **feature_list.json é inviolável** — não remova nem edite steps existentes
5. **claude-progress.txt só cresce** — nunca sobrescreva entradas anteriores
6. **Modo real requer confirmação explícita** — LIVE_TRADING_ENABLED=true só com intenção consciente

---

## Camadas de segurança (execution_engine)

```
Ordem recebida
     │
     ▼
[1] Validação estrutural (quantity > 0, side válido, price > 0)
     │ falha → status: "rejected", não registra no STORE
     ▼
[2] Guardrail de live trading (LIVE_TRADING_ENABLED)
     │ falha → status: "blocked", não registra no STORE
     ▼
[3] Validação de credenciais (ccxt_binance)
     │ falha → status: "simulated"
     ▼
[4] Execução
     │ paper → status: "executed"
     │ live  → status: "submitted"
```

**Nenhuma ordem com status "rejected" ou "blocked" atualiza posições.**

---

## Estado atual das features

Ver `harness/feature_list.json` para o estado atual de cada feature.

Sumário rápido:
```bash
python3 -c "
import json
with open('harness/feature_list.json') as f:
    data = json.load(f)
passing = sum(1 for f in data['features'] if f['passes'])
total = len(data['features'])
print(f'Passing: {passing}/{total}')
for f in data['features']:
    status = '✅' if f['passes'] else '❌'
    print(f'  {status} {f[\"id\"]} [{f[\"category\"]}]: {f[\"description\"][:60]}')
"
```

---

## Bugs conhecidos e pendentes

| ID | Bug | Feature | Prioridade |
|---|---|---|---|
| B001 | STORE in-memory — perde estado no restart | F002 | Alta |
| B002 | avg_price sobrescreve (não VWAP) | F014 | Alta |
| B003 | unrealized_pnl usa 1% fixo | F016 | Média |
| B004 | signal_engine usa math.sin — sem dados reais | F004-F006 | Média |
| B005 | Sem scheduler recorrente real (manual only) | F017 | Baixa |

---

## Como adicionar uma nova feature ao feature_list

```json
{
  "id": "F021",
  "category": "signal_engine",
  "description": "Sinal gerado com dados OHLCV reais via yfinance",
  "steps": [
    "POST /signals/generate para BTCUSDT",
    "Verificar que price != 85000.0 (preço real do mercado)",
    "Verificar que prob_up é derivado de indicadores reais (RSI, EMA)",
    "Verificar que action muda entre timeframes diferentes"
  ],
  "passes": false,
  "notes": ""
}
```

Adicione ao final do array `features`. Nunca reordene.
