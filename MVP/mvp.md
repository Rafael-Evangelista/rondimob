# Rondimob — Especificação Detalhada do MVP

## 1. Visão do MVP

O Rondimob será uma plataforma de monitoramento imobiliário que coleta anúncios de fontes selecionadas, identifica novos imóveis e alterações relevantes, organiza os dados e apresenta oportunidades em um dashboard.

### Fluxo principal

Sites/fontes imobiliárias
→ Scrapers Python
→ Normalização dos dadosf
→ PostgreSQL
→ Detecção de mudanças
→ API FastAPI
→ Dashboard
→ Alertas

O MVP deve responder:

1. Quais imóveis novos apareceram?
2. Quais imóveis tiveram alteração de preço?
3. Quais imóveis atendem aos filtros configurados?
4. O que mudou desde a última coleta?

---

## 2. Priorização das funcionalidades

| Prioridade | Feature | MVP | Importância |
|---|---|---|---|
| P0 | Cadastro/login | Sim | Essencial |
| P0 | Configuração de regiões/filtros | Sim | Essencial |
| P0 | Coleta automática de anúncios | Sim | Essencial |
| P0 | Normalização dos imóveis | Sim | Essencial |
| P0 | Detecção de novos imóveis | Sim | Essencial |
| P0 | Detecção de alteração de preço | Sim | Essencial |
| P0 | Dashboard de oportunidades | Sim | Essencial |
| P1 | Alertas por e-mail | Sim | Alto valor |
| P1 | Alertas por WhatsApp | Depois | Alto valor |
| P1 | Favoritar imóveis | Sim | Alto valor |
| P1 | Histórico de preço | Sim | Diferencial |
| P2 | Score de oportunidade | Depois | Diferencial |
| P2 | IA para análise | Depois | Diferencial |
| P2 | CRM de leads | Não | Fora do MVP |
| P2 | App mobile | Não | Fora do MVP |

---

# 3. Feature P0 — Cadastro e autenticação

## Objetivo

Permitir que cada imobiliária tenha uma conta e mantenha suas configurações isoladas.

## Escopo

- Cadastro
- Login
- Logout
- Recuperação de senha
- Identificação da imobiliária
- Usuário administrador

Não incluir inicialmente:

- SSO
- Login social
- RBAC avançado
- múltiplos níveis de permissão

## Critérios de sucesso

- Usuário consegue criar conta.
- Usuário consegue fazer login.
- Usuário consegue recuperar a senha.
- Dados de uma imobiliária não aparecem para outra.
- Sessão é mantida de forma segura.

**Prioridade: P0**

---

# 4. Feature P0 — Configuração do radar

O usuário deve conseguir definir exatamente o que deseja monitorar.

## Exemplo

**Radar:** Moema até 800k

- Região: Moema
- Tipo: Apartamento
- Preço: R$ 300.000 a R$ 800.000
- Quartos: 2+
- Área: 60 m²+
- Vagas: 1+

O usuário poderá criar mais de um radar.

## Filtros iniciais

- Cidade
- Bairro
- Tipo do imóvel
- Preço mínimo/máximo
- Área mínima/máxima
- Quartos
- Vagas

## Critério de sucesso

O usuário deve conseguir criar um radar em menos de 2 minutos.

**Prioridade: P0**

---

# 5. Feature P0 — Coleta automática de anúncios

Será o principal componente técnico do produto.

O Rondimob terá scrapers em Python para coletar anúncios de fontes previamente selecionadas.

## Dados mínimos

- Título
- URL
- Preço
- Tipo
- Endereço/região
- Bairro
- Cidade
- Área
- Quartos
- Banheiros
- Vagas
- Descrição
- Imobiliária/anunciante
- Data da coleta
- Fonte

Quando disponível:

- Condomínio
- IPTU
- Latitude
- Longitude
- Imagens
- Código do anúncio

## Arquitetura sugerida

```text
scrapers/
├── base.py
├── source_a.py
├── source_b.py
└── source_c.py
```

Cada fonte deve ser independente para facilitar manutenção.

## Critérios de sucesso

Para cada fonte suportada:

- Coleta automática funcionando.
- Dados principais preenchidos.
- Duplicações controladas.
- Erros registrados.
- Falha de uma fonte não derruba o restante do sistema.

**Meta inicial:** 95% das execuções sem erro crítico.

**Prioridade: P0**

---

# 6. Feature P0 — Normalização dos dados

Diferentes fontes podem apresentar os mesmos dados de formas diferentes.

Exemplo:

```text
R$ 650.000
650 mil
650000
R$ 650 mil
```

Tudo deve virar:

```text
650000
```

## Normalizações necessárias

- Preço
- Área
- Quartos
- Banheiros
- Vagas
- Bairro
- Cidade
- Tipo de imóvel

## Critérios de sucesso

- Preço corretamente convertido.
- Área corretamente convertida.
- Quartos corretamente identificados.
- Bairro/cidade padronizados.
- Tipo de imóvel padronizado.

**Prioridade: P0**

---

# 7. Feature P0 — Detecção de novos anúncios

O sistema deve comparar a coleta atual com os registros anteriores.

Exemplo:

```text
Ontem: 100 anúncios
Hoje: 107 anúncios

Resultado:
7 novos imóveis
```

## Identificação

Priorizar:

```text
source + external_id
```

Quando não existir ID confiável:

```text
hash(URL)
```

Pode ser utilizado também um identificador composto por características do imóvel.

## Critérios de sucesso

- Novo anúncio é identificado como novo.
- Anúncio não é duplicado em cada execução.
- Novo anúncio aparece no radar correspondente.

**Prioridade: P0**

---

# 8. Feature P0 — Detecção de alteração de preço

Exemplo:

```text
01/09 — R$ 650.000
08/09 — R$ 620.000
15/09 — R$ 590.000
```

Resultado:

```text
Redução: R$ 60.000
Percentual: -9,2%
```

## Dashboard

```text
REDUÇÃO DE PREÇO

Apartamento 2 dorms
Moema

Antes: R$ 650.000
Agora: R$ 590.000

↓ 9,2%

Ver anúncio
```

## Critérios de sucesso

O sistema deve:

- Identificar alteração.
- Armazenar valor anterior.
- Armazenar valor novo.
- Calcular diferença.
- Calcular percentual.
- Registrar data.

**Prioridade: P0**

---

# 9. Feature P0 — Dashboard

O dashboard será a principal interface do MVP.

## Tela inicial

```text
Rondimob

37 novos
12 quedas de preço
8 oportunidades

Novos imóveis

R$ 480k | 2 dorm | Moema
R$ 520k | 3 dorm | Saúde
R$ 610k | 2 dorm | Vila Mariana
```

## Filtros

- Radar
- Bairro
- Preço
- Tipo
- Quartos
- Área
- Somente novos
- Somente redução de preço

## Critério de sucesso

O usuário deve conseguir:

**abrir → filtrar → encontrar imóvel → abrir anúncio**

em poucos cliques.

Meta inicial: 90% dos usuários conseguem encontrar uma oportunidade relevante sem treinamento.

**Prioridade: P0**

---

# 10. Feature P1 — Histórico de preço

Guardar o histórico permite mostrar a evolução do preço.

Exemplo:

```text
R$ 720k
   ↓
R$ 690k
   ↓
R$ 650k
   ↓
R$ 599k
```

## Estrutura

```text
price_history

property_id
price
captured_at
```

## Critério de sucesso

Para anúncios monitorados, o sistema deve conseguir reconstruir corretamente a sequência de preços.

**Prioridade: P1**

---

# 11. Feature P1 — Alertas

O usuário não deve precisar abrir o sistema diariamente.

## Exemplo

```text
5 novas oportunidades encontradas

Radar: Moema até R$ 800k

3 novos imóveis
2 reduções de preço

Maior redução:
R$ 720k → R$ 650k
-9,7%
```

## MVP

Começar por e-mail.

WhatsApp pode ser implementado posteriormente.

## Configuração

```text
[x] Novos imóveis
[x] Redução de preço

Frequência:
○ Imediatamente
● 1x por dia
○ 1x por semana
```

## Critérios de sucesso

- Alerta chega ao destinatário.
- Informações estão corretas.
- Link abre o anúncio.
- Não há duplicações excessivas.

**Prioridade: P1**

---

# 12. Feature P1 — Favoritos

Permitir salvar imóveis importantes.

```text
⭐ Favorito

Apartamento Moema
R$ 590.000

[Ver anúncio]
```

## Critérios

O usuário consegue:

- Favoritar.
- Desfavoritar.
- Visualizar favoritos.
- Acessar anúncio original.

**Prioridade: P1**

---

# 13. Feature P2 — Score de oportunidade

Não é necessário para o primeiro lançamento, mas a arquitetura deve permitir sua inclusão.

Exemplo:

```text
Score: 87/100
```

Baseado em fatores objetivos:

- Preço abaixo da média
- Redução recente
- Preço/m² competitivo
- Localização
- Tempo anunciado

O score deve ser explicável e reproduzível.

**Prioridade: P2**

---

# 14. Feature P2 — IA

A IA deve entrar depois da validação do produto.

## Possibilidades

### Resumo automático

> Apartamento de 72 m² em Moema, 2 dormitórios e 1 vaga. O anúncio sofreu redução de R$ 60 mil nos últimos 14 dias.

### Perguntas

```text
Esse imóvel teve redução?

Qual o preço por m²?

Está abaixo da média dos imóveis semelhantes?
```

Inicialmente, priorizar regras e cálculos determinísticos. LLM deve ser adicionada depois que existir volume suficiente de dados.

**Prioridade: P2**

---

# 15. O que NÃO colocar no MVP

Para manter o projeto viável para uma pessoa desenvolver:

- CRM completo
- Gestão de leads
- Pipeline comercial
- Chatbot imobiliário
- Aplicativo mobile
- Machine Learning
- 20+ fontes de dados
- Integração com todos os portais
- Gestão completa dos imóveis da imobiliária
- Automação comercial complexa

O Rondimob não precisa substituir o sistema imobiliário do cliente.

---

# 16. Arquitetura inicial

```text
                    ┌──────────────────┐
                    │ Sites / Fontes   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Python Scrapers  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Normalização     │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ PostgreSQL       │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ FastAPI          │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Angular          │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Usuário          │
                    └──────────────────┘
```

## Stack sugerida

### Frontend

Angular

### Backend

Python + FastAPI

### Scraping

Python + BeautifulSoup / Playwright

### Banco

PostgreSQL

### Jobs

Inicialmente:

- cron

Posteriormente:

- Celery + Redis

### Infraestrutura

Docker

### IA

Adicionar em uma segunda etapa.

---

# 17. Critérios gerais de sucesso do MVP

## Produto

Meta inicial:

- 3–5 fontes funcionando.
- 1.000+ anúncios monitorados.
- Novos anúncios identificados corretamente.
- Alterações de preço identificadas.
- Dashboard funcionando.
- Alertas funcionando.

## Validação comercial

Objetivo inicial:

**5–10 imobiliárias utilizando o produto de verdade.**

Mais importante que quantidade de usuários:

> Algumas imobiliárias devem utilizar o radar semanalmente para encontrar oportunidades.

## Retenção

O fluxo esperado:

```text
Cliente entra
     ↓
Configura radar
     ↓
Recebe oportunidades
     ↓
Volta ao sistema
     ↓
Utiliza novamente
```

Se o cliente não voltar, o problema pode estar no valor percebido e não na tecnologia.

---

# 18. MVP mínimo recomendado

Para lançar rapidamente como desenvolvedor solo:

```text
1. Cadastro/login
        ↓
2. Criar radar
        ↓
3. Scraper Python
        ↓
4. Normalização
        ↓
5. PostgreSQL
        ↓
6. Detecção de novos/preço
        ↓
7. Dashboard
        ↓
8. E-mail diário
```

## Primeira versão prática

Começar com:

**1 nicho + 2 ou 3 fontes + 1 tipo de imóvel + 1 região + dashboard + alerta por e-mail.**

Depois da validação:

1. Mais fontes.
2. Mais regiões.
3. Histórico de preços.
4. Score de oportunidade.
5. WhatsApp.
6. IA.
7. Funcionalidades comerciais.

---

# 19. Princípio do produto

O produto inicial deve ser simples:

> **"Eu monitoro o mercado imobiliário para você e aviso quando aparece algo relevante."**

A IA deve entrar posteriormente para transformar o volume de dados coletados em inteligência comercial.
