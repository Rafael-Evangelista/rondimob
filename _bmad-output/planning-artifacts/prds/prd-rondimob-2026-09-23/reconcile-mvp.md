---
title: rondimob MVP ↔ PRD reconcile
status: draft
created: 2026-09-23
updated: 2026-09-23
inputs:
  - MVP/mvp.md
  - prd.md
  - addendum.md
note: Gaps are MVP requirements the PRD dropped. User overrides (ABCD, CRECI/PJ, same view, trial/plans, no dark UI, RAG/fine-tuning later, stack Django) are excluded.
---

# Reconcile MVP → PRD

## Gaps

1. **Meta de usabilidade do dashboard (90%)** — MVP §9 exige que ~90% dos usuários encontrem uma oportunidade relevante sem treinamento. O PRD (FR-8 / SM) mantém só o caminho “abrir → filtrar → encontrar → abrir”, sem essa meta qualitativa.

2. **Princípio / tom do produto** — MVP §19 fixa a promessa: *“Eu monitoro o mercado imobiliário para você e aviso quando aparece algo relevante.”* O PRD troca o tom por “preço por região e concorrentes no ABCD”; a frase-guia de monitoramento + aviso some da visão e dos critérios de sucesso.

3. **Sessão segura como critério de auth** — MVP §3 lista “sessão mantida de forma segura” entre os critérios de sucesso de cadastro/login. FR-2 cobre criar conta, login, logout e recuperação de senha, mas não carrega esse critério.

4. **Configuração de alertas (tipos e frequência)** — MVP §11 pede UI para escolher novos / redução de preço e frequência (imediato, 1×/dia, 1×/semana). FR-10 fixa e-mail diário e diz que o e-mail “pode incluir” os tipos, sem requisito de configuração pelo usuário.

5. **Bairro como filtro do radar** — MVP §4 inclui bairro nos filtros iniciais do radar. FR-5 cria radar com cidade do ABCD, imobiliária anunciante, tipo, preço, área, quartos e vagas — sem bairro na criação (só no filtro da área do cliente, FR-8).
