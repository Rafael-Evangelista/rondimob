---
title: rondimob PRD addendum
status: draft
created: 2026-09-23
updated: 2026-09-23
---

# Addendum — decisões que não moram no PRD

## Stack confirmada pelo usuário em 2026-09-23

Django + PostgreSQL + Celery/Redis. Worker em processo separado, uma fila por fonte. Anúncios compartilhados; isolamento nas tabelas privadas da imobiliária com row-level security forçado. django-tenants fica fora do primeiro dia.

Fonte da escolha: `_bmad-output/planning-artifacts/research/technical-stack-mvp-saas-imobiliario-multi-tenant-2026-09-23/research.md`.

O esboço em `MVP/mvp.md` ainda cita FastAPI e Angular. Essa pilha foi substituída por esta decisão. O comportamento do produto no esboço continua como insumo do PRD; o transporte HTTP e o framework de tela não.

## Ambição técnica de origem

Em 2026-09-23 o usuário disse que a ideia nasceu com um chat de IA e que a vontade era criar algo útil com scraping, RAG e fine tuning. O chat ajudou a chegar na ideia que ele está colocando em prática. RAG e fine tuning ainda não são requisito desta versão. O scraping já está no comportamento do MVP.

## Direção visual para o UX

Em 2026-09-23 o usuário pediu para não usar cores escuras, porque o sistema é para imobiliária. A interface deve se adequar aos padrões de cor usados em SaaS e em sistemas imobiliários, com um toque mais moderno, sem ficar engessada. A paleta concreta não foi escolhida aqui. O desenho de UX parte dessa direção e não introduz tema escuro como base.
