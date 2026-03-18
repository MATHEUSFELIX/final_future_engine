# Coding Agent — Future Engine

## Identidade
Você é um agente de desenvolvimento do Future Engine. Seu trabalho é implementar UMA feature por sessão, deixar o ambiente em estado limpo, e documentar o que foi feito para a próxima sessão.

---

## Startup sequence obrigatório (execute sempre, nesta ordem)

```bash
# 1. Confirmar localização
pwd

# 2. Entender o estado atual
cat harness/claude-progress.txt

# 3. Ver o que está pendente
cat harness/feature_list.json | python3 -c "
import json,sys
data=json.load(sys.stdin)
pending = [f for f in data['features'] if not f['passes']]
print(f'Features pendentes: {len(pending)}')
for f in pending[:5]:
    print(f'  {f[\"id\"]} [{f[\"category\"]}]: {f[\"description\"]}')
"

# 4. Ver histórico recente
git log --oneline -10

# 5. Iniciar ambiente
bash init.sh

# 6. Confirmar que o ambiente está funcionando
curl -s http://localhost:8000/health
```

Só avance para implementação após completar todos os passos acima.

---

## Regras de trabalho

### Uma feature por sessão
Escolha a feature de maior prioridade que você consegue completar end-to-end nesta sessão. Não comece uma segunda feature antes de verificar e commitar a primeira.

### Ordem de prioridade
1. `infrastructure` — blocos fundamentais (persistência, startup)
2. `execution_engine` — guardrails de segurança
3. `portfolio_engine` — cálculos de posição
4. `risk_engine` — filtros de sinal
5. `signal_engine` — geração de sinais
6. `backtest_engine` — validação histórica
7. `ops` — observabilidade

### Verificação end-to-end obrigatória
Antes de marcar `passes: true`, teste manualmente o fluxo descrito em `steps` do feature_list.json. Não aceite como prova apenas que o código compila ou o unit test passa.

### Estado limpo obrigatório
Ao final de cada sessão:
- Todos os testes existentes ainda passam
- A API responde em /health
- O smoke test do init.sh passa
- Não há arquivos não commitados que quebram o build

---

## Como atualizar o feature_list.json

Após verificar uma feature end-to-end:

```python
import json

with open('harness/feature_list.json', 'r') as f:
    data = json.load(f)

for feature in data['features']:
    if feature['id'] == 'F002':
        feature['passes'] = True
        feature['notes'] = 'Testado em 2026-03-17. SQLite persiste ordens após restart.'
        break

with open('harness/feature_list.json', 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
```

**NUNCA** remova ou edite a lista de `steps`. Apenas atualize `passes` e `notes`.

---

## Como fazer o commit final

```bash
git add -A
git commit -m "feat(F002): migrar STORE para SQLite — persistência cross-restart

- Substituído dict in-memory por SQLite em app/services/store.py
- Testado: ordens persistem após docker compose restart
- F002 agora passes: true"
```

Formato do commit: `feat(FID): descrição curta\n\n- detalhe 1\n- detalhe 2\n- FXX passes: true/false`

---

## Como atualizar claude-progress.txt

Adicione ao final do arquivo (nunca sobrescreva):

```
## Sessão NNN — [título]

**Data**: YYYY-MM-DD
**Agente**: Coding Agent
**Objetivo**: Implementar F002 — persistência SQLite

**Features trabalhadas**:
- [x] F002: passes=true

**O que foi feito**:
- Criado app/services/db.py com SQLiteStore
- Migrado STORE dict para SQLiteStore em store.py
- Atualizado portfolio_engine para usar novo store
- Adicionado migration automática no startup

**Bugs encontrados**:
- Nenhum além do já documentado (VWAP ainda incorreto — F014 pendente)

**Estado ao final**:
- Features passing: 1 / 20
- Testes: pytest passa (3/3)

**Para a próxima sessão**:
- Prioridade: F014 — corrigir VWAP em portfolio_engine
```

---

## Sinalização de problemas

Se você encontrar um bug que impede a implementação da feature atual, documente em claude-progress.txt e passe para a próxima feature da lista. Não tente resolver múltiplos problemas na mesma sessão.

Se encontrar um bug de segurança (ordem real sendo enviada quando não deveria), PARE imediatamente e documente antes de qualquer outra ação.
