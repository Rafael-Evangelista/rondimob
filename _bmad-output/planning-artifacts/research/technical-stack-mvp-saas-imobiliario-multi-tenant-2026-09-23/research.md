---
title: 'pesquisa técnica: stack do MVP para um SaaS imobiliário multi-tenant'
type: 'technical'
topic: 'stack do MVP para um SaaS imobiliário multi-tenant'
decision: 'Escolher a stack do MVP para que um monitor imobiliário possa virar um SaaS multi-tenant (uma conta por imobiliária, isolamento de dados), comparando corpus compartilhado de anúncios com coleta por imobiliária. Sem começar o desenvolvimento.'
source: 'native-run'
status: complete
preset: 'standard'
validation: 'normal'
created: '2026-09-23'
updated: '2026-09-23'
language: 'Portuguese'
---

# Pesquisa técnica: stack do MVP para um SaaS imobiliário multi-tenant

**Decisão que esta pesquisa serve:** escolher a stack do MVP para que um monitor imobiliário possa virar um SaaS multi-tenant (uma conta por imobiliária, isolamento de dados), comparando um corpus compartilhado de anúncios com coleta por imobiliária. Sem começar o desenvolvimento.

## Resumo executivo

Começar pelo modelo de dados, não pelo framework. O corpus de anúncios é compartilhado; radares, favoritos, alertas e configuração são privados. No PostgreSQL isso é row-level security por tabela: a tabela de anúncios fica sem RLS (ou com leitura aberta), e as tabelas privadas usam `ENABLE` e `FORCE ROW LEVEL SECURITY` [13]. O dono da tabela ignora o RLS se o `FORCE` não estiver ligado [13]. Em pooler no modo transação, `SET`/`RESET` de sessão é incompatível [14]; o contexto do tenant tem de nascer dentro da transação.

A stack que melhor carrega isso, com a evidência desta rodada, é **Django + PostgreSQL + Celery/Redis**, com o worker em processo separado e uma fila por fonte [26][27]. O pacote django-tenants, que empurra schema por tenant, fica de fora do padrão do primeiro dia [15][11]. A segunda colocada é **Next.js + Supabase + Trigger.dev**: o RLS já é o isolamento documentado do Supabase [17], e as tarefas não têm timeout [22], mas a saída da plataforma é parcial [30] e um incidente de junho de 2026 segurou filas por muitas horas [24]. Os pesos desta leitura dão 355 a 315, numa escala de 500. Não é medição.

FastAPI continua viável no mesmo desenho de banco e worker, com confiança baixa na montagem completa: a página de um relato solo não abriu nesta conferência. Rails só entra se já houver fluência [1]. A UI do dashboard continua em aberto.

Custo de validação, lido ao vivo em 2026-09-23: cerca de US$ 55/mês com um banco (Vercel Pro US$ 20 + Supabase US$ 25 + Trigger.dev US$ 10 + e-mail grátis) e cerca de US$ 145/mês com dez bancos pequenos na Supabase [19][20][22]. Os dois cabem no portão de custo. O modelo de um banco por imobiliária não perde por ser impagável nessa escala; perde porque o produto é um corpus compartilhado e porque a coleta duplicada não tem preço medido.

A ressalva maior: não há retrospectiva de 6–12 meses de um monitor de anúncios com Playwright. O que existe é o mecanismo (processo e fila separados) e relatos de SaaS adjacentes.

## Enquadramento dos requisitos

Portões duros (passa ou cai):

1. Um desenvolvedor solo entrega cadastro, filtros de radar, coleta, normalização, detecção de mudança, dashboard e alertas por e-mail.
2. Os dados privados de uma imobiliária ficam isolados desde o primeiro deploy.
3. A falha do scraper de uma fonte não derruba as outras contas.
4. O modelo de tenancy cresce (mais imobiliárias, fontes, histórico de preço, score) sem reescrita do tenancy.
5. O custo cabe na escala de validação: cerca de 5–10 imobiliárias e milhares de anúncios.

Pesos: isolamento e os dois modelos de dados 30; carga do desenvolvedor solo 25; coleta e jobs 20; custo de saída 15; saúde do ecossistema 10.

Os dois modelos de dados estão no escopo, sem escolha prévia: (A) corpus de anúncios compartilhado, com radares, favoritos, alertas e configuração privados por imobiliária; (B) banco e coleta próprios por imobiliária.

A stack do esboço (scrapers Python, FastAPI, Angular, PostgreSQL, cron e depois Celery/Redis, Docker) é uma candidata de partida. Não é evidência e não é portão duro.

## Triagem de candidatas

Parou no teto de rodadas (2 de 2). As perguntas da triagem estão respondidas o bastante para travar os finalistas. O que ficou em aberto alimenta arquitetura, implementação e custo.

### Stacks finalistas

NestJS sai. A rodada 1 só o encontrou como nome de opção de backend, sem retrospectiva de produção [2].

1. **Next.js + Supabase (Postgres, Auth, RLS) + um runner de jobs gerenciado.** Um panorama de stacks de maio de 2026 aponta isso para times solo e pequenos [1]. Um guia de arquitetura de março de 2026 trata row-level security no Postgres como o começo multi-tenant, e diz que um schema compartilhado ainda funciona na casa das dezenas de milhares de tenants [2]. Confiança média: os dois editores são um fornecedor de kit e uma consultoria.

2. **Django + PostgreSQL + Celery/Redis, web e workers em processos separados.** Um relato de produção de abril de 2026 trata Celery e Redis como o caminho para tirar trabalho agendado do request, e manda separar filas para o volume não bloquear o que é crítico [6]. O mesmo panorama de maio ainda chama Django de alternativa produtiva para SaaS [1]. Confiança média.

3. **Laravel + PostgreSQL + filas Redis.** Um relato em primeira pessoa (junho de 2026, atualizado em agosto de 2026) descreve um SaaS Laravel multi-tenant com mais de 200 unidades, começando em tabelas compartilhadas com `tenant_id` e levando um cliente exigente para um banco dedicado depois [5]. Confiança média-alta nesse caminho; é um único autor.

4. **FastAPI + PostgreSQL + um worker separado + uma UI web.** Esta é a candidata do esboço. Um artigo de abril de 2026, conferido nesta rodada, mostra FastAPI com schemas por tenant e tabelas compartilhadas em `public` via `search_path` [8]. Esse artigo não menciona workers. Nenhuma fonte única datada de 2026-03-23 em diante documenta FastAPI, PostgreSQL, workers em background e multi-tenancy juntos. A ausência não reprova o portão, então a stack permanece. Confiança média no pedaço de tenancy, baixa na montagem completa.

5. **Curinga: Rails, se quem constrói sozinho já tiver fluência.** O panorama de maio diz para usar Rails quando o time já domina a ferramenta [1]. Retrospectivas recentes com números de produção ficaram ralas. Confiança baixa.

Angular não é uma stack à parte. A objeção de mercado de contratação nesse panorama [1] não é um dos portões duros. A UI do dashboard continua uma escolha aberta dentro destas cinco.

### Padrões de tenancy

**Modelo A — um corpus de anúncios compartilhado, com sobreposições privadas por imobiliária.** O tutorial de Postgres multi-tenant da Microsoft descreve tabelas de referência: linhas que pertencem a todos os tenants, guardadas como cópia sincronizada em cada worker, enquanto as tabelas do tenant são distribuídas por uma chave de tenant [7]. Uma conferência confirmou esse mecanismo. A busca não mostrou data de publicação, então o frescor da página segue sem verificação. O mesmo corte aparece no código de aplicação como tabelas compartilhadas em `public` mais schemas por tenant [8]. A orientação que põe `tenant_id` em toda tabela [9] não serve para um catálogo compartilhado. O modelo A precisa de duas políticas: anúncios legíveis entre imobiliárias, e row-level security em radares, favoritos, alertas e configuração.

**Modelo B — um banco por imobiliária.** Uma query ruim ou uma credencial comprometida atinge um tenant [9]. Em cerca de 50 tenants, o composto desse fornecedor coloca banco-por-tenant em US$ 2.000–4.500 por mês e 4–8 horas por semana de DevOps, contra US$ 400–900 por mês para um schema compartilhado [9]. Um segundo fornecedor, com linhas de base por tenant checadas em abril de 2026, coloca um Postgres gerenciado dedicado em US$ 40–120 por tenant por mês, antes de compute [12]. Cinquenta vezes essa faixa é a mesma ordem de grandeza. Conferência: verificado em direção e ordem. As duas datas são mais velhas que a barra de preço de três meses (acesso em 2026-09-23; a barra abre em 2026-06-23), então os dólares estão velhos. A seção de custo relê as páginas de preço ao vivo. Em 5–10 imobiliárias o custo linear ainda pode passar no portão de custo; isso não se fecha aqui.

**Híbrido — compartilhado primeiro, banco dedicado para um tenant exigente depois** [5][3]. Esse é o caminho de crescimento. Não é o formato do primeiro dia para uma validação solo.

**Schema por tenant sai como padrão do primeiro dia.** Um relato de produção de 12 de setembro de 2026 descreve migrações que precisam ter sucesso uma vez por tenant, e uma falha parcial que deixa a frota dividida (o exemplo é o tenant 247 de 500), a menos que se acrescentem um registro, um livro-razão e rollouts em ondas [11]. Fonte única, sem conferência. Um post de engenharia de maio de 2026 diz que schema por tenant raramente é a escolha certa [3]. Uma consultoria de março de 2026 ainda o oferece para cerca de 50–500 tenants com muita customização [2]. A contradição permanece. Para 5–10 imobiliárias no mesmo produto, não é o padrão.

**Banco por tenant para toda imobiliária no primeiro dia sai como padrão.** Os números de custo reprovam esse padrão universal [9][12]. O modelo B fica na matriz como a opção de isolamento forte, não como o formato de partida.

### O que não ficou estabelecido

Nenhuma fonte recente precifica o desperdício de raspar os mesmos sites públicos de anúncio uma vez por imobiliária. Uma comparação de setembro de 2026 entre raspagem de logs por tenant e raspagem compartilhada [10] é outro domínio e não entra como evidência sobre sites de anúncio. Nenhuma fonte de 2026-08-23 em diante fixou números de versão de framework.

## Padrões de arquitetura

Parou na primeira rodada por cobertura. A pergunta de como o modelo A cabe no Postgres está respondida em documentação oficial, relida nesta conferência.

O RLS começa desligado. Quem tem `GRANT` vê todas as linhas. Ele passa a valer só depois de `ALTER TABLE … ENABLE ROW LEVEL SECURITY` naquela tabela, e cada política é da tabela [13]. O mesmo manual está na trilha `current` [4]. Dá para deixar anúncios sem RLS e ligar RLS só em radares, favoritos, alertas e configuração.

O furo documentado: superusuário e papel com `BYPASSRLS` sempre passam. O dono da tabela também passa, até `ALTER TABLE … FORCE ROW LEVEL SECURITY` [13]. `ENABLE` sozinho não isola se a aplicação conecta como dona.

No PgBouncer, modo transação, a coluna `SET/RESET` está marcada **Never** [14]. Um `SET` de sessão com o id do tenant pode sobreviver ao fim do request e cair no próximo cliente da mesma conexão. Não apareceu postmortem datado de 2026-03-23 em diante; o que há é a tabela oficial de incompatibilidade.

Os pacotes divergem, e as páginas abaixo não têm data visível:

- Django, no núcleo, não escolhe um modelo. O django-tenants implementa schema por tenant e também aplicações compartilhadas em `public` [15]. Isso se parece com o modelo A, e é o padrão que a triagem tirou do primeiro dia por causa da dor de migração na casa das centenas [11].
- Laravel, no caminho de início do stancl/tenancy, é multi-banco [16]. Serve o modelo B. O atalho do dia 1 desse pacote não é o corpus compartilhado.
- Supabase trata RLS como o isolamento das tabelas expostas: tabela sem RLS fica legível por qualquer papel com grant [17].

O único número de produção sobre “o que quebra primeiro” é um relato sem data visível: uma política de RLS com subconsulta levou o p95 de 9 ms a 1,4 s numa tabela de cerca de 40 milhões de linhas, e o pool enfileirou porque as sessões seguravam a conexão cerca de 100 vezes mais [18]. Frescor baixo. Não decide a stack. Serve de alerta: política de RLS com subconsulta é o formato que doeu; a troca citada foi `tenant_id = current_setting(...)` mais `FORCE`.

## Realidade de implementação

Parou na primeira rodada. Uma segunda abertura do relato FastAPI estourou o tempo, então esse vazio continua.

O relato solo mais próximo, dentro da janela, é um SaaS Django + React + Celery + Postgres (2026-03-23, atualizado em 2026-04-09): meses em tempo integral até o MVP, mais de 50 mil linhas, mais de 30 tipos de task Celery, filtro de tenant obrigatório no ORM com teste de vazamento, e arrependimento de manter dois pipelines de deploy [23]. É um produto maior que este radar. Mostra que a pilha entrega multi-tenant e jobs; não mede o custo deste MVP.

Do lado Next.js + runner gerenciado, o registro fresco é incidente do fornecedor, não diário de quem constrói sozinho. Em 22–23 de junho de 2026 o Trigger.dev teve dequeue lento e queda em us-east-1 e depois eu-central-1, com dezenas de milhares de organizações afetadas; runs não se perderam, a espera foi longa [24].

No Laravel, um texto de 13 de setembro de 2026 diz que app solo com uma fila modesta deve ficar em `queue:work` sob Supervisor, e que Horizon acrescenta acoplamento a Redis, superfície de autenticação do painel e mais um processo para vigiar [25]. É ensaio de operação, não retrospectiva com incidente.

Isolamento do scraper: o guia de workers do Celery trata cada worker como processo à parte [26]. O guia de roteamento mostra uma fila `feeds` e um worker com `-Q feeds`, para essa classe de trabalho não dividir consumidor com o resto [27]. Isso sustenta o portão 3 no plano do processo: o crash do browser mata o worker, não o HTTP, se os processos forem separados, e uma fonte quebrada não esgota as outras filas se o roteamento existir. Não há número de crash de Playwright em produção nesta rodada.

Carga de RLS: um relato de 24 de junho de 2026 opera Supabase com RLS em 69 tabelas e 280 políticas, e trata a suíte pgTAP (permite e nega) como condição para confiar no RLS [28]. O lado Django do outro relato usa filtro no ORM e teste de vazamento [23]. Não há comparativo direto de meses de operação entre os dois.

E-mail diário: a documentação do Resend guarda chave de idempotência por 24 horas e devolve o resultado anterior sem reenviar [31]. A implicação prática é marcar o digest com uma chave de negócio antes do envio, porque redrive tarde duplica a mensagem. Isso não separa as stacks.

Rails e a montagem completa FastAPI + worker + multi-tenant: sem retrospectiva lida até o fim nesta rodada.

## Custo e aprisionamento

Parou na primeira rodada. Os preços abaixo foram lidos em páginas oficiais em 2026-09-23. Nenhuma dessas páginas mostrou data de publicação. A conta da Supabase, o Pro da Vercel e a frase de timeout do Trigger.dev foram relidas nesta conferência. Os compostos de maio e abril (US$ 2.000–4.500 e US$ 40–120) continuam velhos para a barra de três meses e não entram na conta [9][12].

| Peça | Preço usado | Fonte |
| --- | --- | --- |
| Supabase Pro | US$ 25/mês, mais compute por projeto | [19] |
| Micro da Supabase | US$ 10/mês; o Pro inclui US$ 10 de crédito, o que cobre um Micro | [19] |
| Vercel Pro | US$ 20/mês; Hobby é uso pessoal, não comercial | [20] |
| Trigger.dev | faixa de US$ 10/mês; tarefas sem timeout | [22] |
| Resend | grátis até 3.000 e-mails/mês e 100/dia | [29] |

Um banco compartilhado, com e-mail grátis: 20 + 25 + 10 + 0 = **cerca de US$ 55/mês**. Dez projetos Micro: Supabase 25 + (10 × 10) − 10 = 115, mais Vercel 20 e Trigger 10, total **cerca de US$ 145/mês** [19][20][22]. O exemplo oficial de dois Micros fecha em US$ 35 e confirma o crédito [19].

Duração de Function na Vercel, com fluid compute: Hobby no máximo 300 s; Pro no máximo 800 s; acima disso, até 1800 s, está em beta [32]. Uma coleta com browser que passe desses tetos morre na Function. O Trigger.dev declara que a tarefa corre pelo tempo que precisar, sem timeout [22]. A coleta longa cabe no worker gerenciado; cabe mal na Function.

Saída da Supabase: o guia oficial cobre `supabase db dump` de papéis, schema, dados, RLS e `auth.users`. Objetos de storage e edge functions ficam de fora. Os JWT são invalidados [30]. Sair para um Postgres sem o stack Supabase (auth e storage) não está especificado nessa página. Saída da Vercel: nenhuma narrativa de migração datada entrou nesta rodada. A evidência de custo de saída da Vercel é rala.

Uma estimativa Railway (app + Postgres + Redis contra dez Postgres) foi calculada na rodada de custo a partir da página de preços e não foi relida aqui. Fica fora do veredito.

## O que as dimensões juntas mostram

O framework é consequência do banco e do worker. RLS por tabela é recurso do PostgreSQL [13], então Django, FastAPI e Rails podem usar o mesmo modelo A. A vantagem da Supabase é o RLS já amarrado ao Auth [17], com o custo de testar política como produto [28] e de uma saída parcial [30].

O portão da coleta elimina rodar o scraper dentro da Function da Vercel quando o trabalho passa de 800 s [32]. Sobrevive quem tem worker sem esse teto: Celery em processo separado [26][27] ou Trigger.dev [22]. O incidente de junho de 2026 mostra o outro lado do worker gerenciado: a espera vira problema de todas as contas ao mesmo tempo [24].

Dez bancos a cerca de US$ 145/mês passam no portão de custo da validação [19]. O modelo B não cai por preço nessa faixa. Cai como formato de partida porque o anúncio é corpus compartilhado e porque a raspagem repetida dos mesmos sites não tem preço medido.

## Evidência contrária

Não houve passagem de red team. O que as fontes já contradizem:

- Schema por tenant é “raramente a escolha certa” num post de maio de 2026 [3] e ainda é oferecido para 50–500 tenants customizados num guia de março [2]. O django-tenants escolhe schema [15].
- Banco por tenant isola melhor o estrago [9] e, a dez Micros, custa cerca de US$ 145/mês e não milhares [19]. O argumento de custo contra o modelo B é mais fraco na escala de validação do que os compostos velhos de 50 tenants sugeriam.
- A pilha com RLS mais documentado para o dia 1 (Supabase) é a que tem saída parcial [30] e incidente de fila em junho de 2026 [24].

## Recomendações

Leitura dos pesos (0 a 5, vezes o peso). Isolamento 30, carga solo 25, coleta e jobs 20, saída 15, ecossistema 10. Máximo 500. Os números são juízo sobre a evidência, não medição.

| Stack | Isol. | Solo | Coleta | Saída | Eco. | Total |
| --- | --- | --- | --- | --- | --- | --- |
| Django + Postgres + Celery/Redis, um schema, RLS nas tabelas privadas | 3 | 3 | 5 | 4 | 3 | 355 |
| Next.js + Supabase + Trigger.dev | 4 | 3 | 3 | 2 | 3 | 315 |
| Laravel + fila simples + Postgres | 2 | 4 | 3 | 4 | 3 | 310 |
| FastAPI + Postgres + worker separado | 3 | 2 | 3 | 4 | 2 | 280 |

Conta: Django 3×30 + 3×25 + 5×20 + 4×15 + 3×10 = 355. Next 4×30 + 3×25 + 3×20 + 2×15 + 3×10 = 315. Laravel 2×30 + 4×25 + 3×20 + 4×15 + 3×10 = 310. FastAPI 3×30 + 2×25 + 3×20 + 4×15 + 2×10 = 280.

**Escolha:** PostgreSQL no modelo A, mais Django, mais Celery e Redis em processo separado, uma fila por fonte. Isolamento nas políticas do banco (`FORCE ROW LEVEL SECURITY` nas tabelas privadas), não no pacote django-tenants [13][15][26][27]. Confiança média: o mecanismo de coleta e o RLS são documentação oficial; o custo solo deste radar em si não foi medido [23].

**Segunda colocada, e quando ela ganha:** Next.js + Supabase + Trigger.dev, se quem constrói quiser Auth e RLS já integrados [17] e aceitar operação de jobs num fornecedor, inclusive o tipo de espera do incidente de junho de 2026 [24], e uma saída que não cobre storage nem um Postgres sem o stack Supabase [30].

**FastAPI** permanece o desenho do esboço no mesmo banco e no mesmo tipo de worker. A confiança na montagem completa fica baixa até existir um relato que una FastAPI, PostgreSQL, worker e multi-tenant. **Rails** só com fluência já existente [1]. **Angular** não foi reprovado pelos portões; a UI segue aberta.

**Hedge mais barato:** políticas de RLS e o worker de coleta não moram no framework HTTP. Trocar Django por FastAPI, ou o contrário, não reescreve o tenancy se o isolamento estiver no Postgres.

Isto fecha a escolha. Não abre implementação.

Alimenta, quando existirem, o eixo de arquitetura (paradigma de tenancy e restrição operacional da coleta) e o brief (viabilidade de um solo na validação).

## Perguntas em aberto

- Preço de raspar os mesmos sites de anúncio uma vez por imobiliária. Sem isso, o modelo B não tem linha de custo de coleta.
- Relato solo de FastAPI + PostgreSQL + worker + multi-tenant. A página candidata não carregou.
- Postmortem datado de vazamento de tenant por `SET` de sessão em pooler. Há a tabela do PgBouncer [14], não o incidente.
- Data de publicação das páginas de preço. Os valores valem para 2026-09-23; a barra de preço pede releitura em três meses.
- Números de versão de framework posteriores a 2026-08-23. Nenhum entrou.

## Fontes (em andamento)

| # | Achado | Editora | Data | Acesso | Confiança |
| --- | --- | --- | --- | --- | --- |
| [1] | Panorama de stack SaaS solo em 2026; Rails se já houver fluência; nota de Angular sobre mercado de contratação | [Makerkit](https://makerkit.dev/blog/saas/saas-stack-2026) | 2026-05-08 | 2026-09-23 | média |
| [2] | Schema compartilhado com RLS até cerca de 10 mil tenants; NestJS só citado; schema por tenant para 50–500 customizados | [Agile Soft Labs](https://www.agilesoftlabs.com/blog/2026/03/best-saas-tech-stack-architecture-2026) | 2026-03-30 | 2026-09-23 | média |
| [3] | Schema compartilhado + id de tenant como padrão de 2026; schema por tenant raramente certo; GUC de tenant no pooler precisa ser da transação | [ClickHouse / Manveer Chawla](https://clickhouse.com/resources/engineering/multi-tenant-saas-postgres-architecture) | 2026-05-25 | 2026-09-23 | média |
| [4] | Mecanismo de RLS: políticas, bypass do dono, negação por padrão | [PostgreSQL Global Development Group](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) | desconhecida | 2026-09-23 | alta (mecanismo); baixa (frescor) |
| [5] | Laravel em produção: mais de 200 unidades; começa compartilhado, banco dedicado depois | [Khawar Hussain](https://khawarr.com/blog/laravel-saas-architecture-guide) | 2026-06-19 | 2026-09-23 | média-alta |
| [6] | Django + Celery + Redis; filas separadas para trabalho em volume | [Softaims](https://softaims.com/blog/django-celery-background-tasks-production-2026) | 2026-04-02 | 2026-09-23 | média |
| [7] | Tabelas de referência para linhas que pertencem a todos os tenants | [Microsoft Learn](https://learn.microsoft.com/en-us/azure/postgresql/configure-maintain/tutorial-multitenant-database) | desconhecida | 2026-09-23 | alta (mecanismo) |
| [8] | FastAPI com schema por tenant + tabelas públicas compartilhadas via search_path; sem workers | [ADHDecode](https://adhdecode.com/articles/fastapi/fastapi-multi-tenancy-implementation/) | 2026-04-16 | 2026-09-23 | média |
| [9] | Cerca de 50 tenants: banco por tenant US$ 2 mil–4,5 mil/mês contra schema compartilhado US$ 400–900/mês | [Acquaint Softtech](https://acquaintsoft.com/blog/multi-tenant-saas-architecture-guide) | 2026-05-15 | 2026-09-23 | média; preço velho |
| [10] | Raspagem de logs por tenant contra raspagem compartilhada (só analogia; não usada para anúncios) | [NHI Mgmt Group](https://nhimg.org/faq/what-is-the-difference-between-per-tenant-log-scraping-and-shared-log-scraping-i/) | 2026-09-10 | 2026-09-23 | baixa (domínio errado) |
| [11] | Dor de migração de schema por tenant na casa das centenas de tenants | [Nas](https://itsnas.me/writing/migrating-schema-per-tenant-databases-at-scale) | 2026-09-12 | 2026-09-23 | média (fonte única, sem conferência) |
| [12] | Postgres gerenciado dedicado a US$ 40–120 por tenant por mês, antes de compute | [MarsDevs](https://www.marsdevs.com/compare/multi-tenant-vs-single-tenant-saas) | 2026-04 | 2026-09-23 | média; preço velho |
| [13] | RLS por tabela; dono ignora RLS até FORCE ROW LEVEL SECURITY | [PostgreSQL 18](https://www.postgresql.org/docs/18/ddl-rowsecurity.html) | desconhecida | 2026-09-23 | alta (mecanismo); relido |
| [14] | SET/RESET incompatível com pooler em modo transação | [PgBouncer](https://www.pgbouncer.org/features.html) | desconhecida | 2026-09-23 | alta; relido |
| [15] | django-tenants é schema por tenant, com apps compartilhados em public | [django-tenants](https://django-tenants.readthedocs.io/en/stable/index.html) | desconhecida | 2026-09-23 | média; frescor baixo |
| [16] | Caminho inicial do stancl/tenancy é multi-banco | [Tenancy for Laravel](https://v4.tenancyforlaravel.com/getting-started/) | desconhecida | 2026-09-23 | média; frescor baixo |
| [17] | Tabela exposta sem RLS fica aberta a quem tem grant | [Supabase](https://supabase.com/docs/guides/database/postgres/row-level-security) | desconhecida | 2026-09-23 | alta (mecanismo) |
| [18] | Política de RLS com subconsulta: p95 de 9 ms a 1,4 s | [MonPG](https://monpg.app/blog/postgresql-row-level-security-performance) | desconhecida | 2026-09-23 | média; frescor baixo |
| [19] | Pro US$ 25; Micro US$ 10; crédito de US$ 10; dois Micros = US$ 35 | [Supabase](https://supabase.com/pricing) | desconhecida | 2026-09-23 | alta; relido |
| [20] | Pro US$ 20/mês; Hobby é uso não comercial | [Vercel](https://vercel.com/pricing) | desconhecida | 2026-09-23 | alta; relido |
| [22] | Faixa de US$ 10/mês; tarefas sem timeout | [Trigger.dev](https://trigger.dev/pricing) | desconhecida | 2026-09-23 | alta; relido |
| [23] | SaaS solo Django+Celery: meses até o MVP, filtro de tenant no ORM | [Faysal](https://byfaysal.com/blog/i-built-hootsuite-competitor-solo) | 2026-03-23 | 2026-09-23 | alta; produto maior que este radar |
| [24] | Incidente de dequeue em 22–23 de junho de 2026 | [Trigger.dev](https://trigger.dev/blog/incident-report-jun-22-2026) | 2026-06-22 | 2026-09-23 | alta |
| [25] | Fila simples basta para app solo; Horizon é carga extra | [Deploynix](https://deploynix.io/blog/do-you-need-laravel-horizon) | 2026-09-13 | 2026-09-23 | média |
| [26] | Worker Celery é processo separado | [Celery](https://docs.celeryq.dev/en/latest/userguide/workers.html) | desconhecida | 2026-09-23 | alta (mecanismo) |
| [27] | Fila dedicada com worker `-Q feeds` | [Celery](https://docs.celeryq.dev/en/stable/userguide/routing.html) | desconhecida | 2026-09-23 | alta (mecanismo) |
| [28] | RLS em 69 tabelas e 280 políticas exige teste pgTAP | [Tomoda Hinata](https://tomodahinata.com/en/blog/supabase-rls-testing-pgtap-policy-regression-guide) | 2026-06-24 | 2026-09-23 | alta |
| [29] | Grátis até 3.000 e-mails/mês e 100/dia | [Resend](https://resend.com/pricing) | desconhecida | 2026-09-23 | alta |
| [30] | Dump cobre RLS e auth.users; storage e edge functions ficam de fora | [Supabase](https://supabase.com/docs/guides/self-hosting/restore-from-platform) | desconhecida | 2026-09-23 | média |
| [31] | Chave de idempotência de e-mail vale 24 h | [Resend](https://resend.com/docs/dashboard/emails/idempotency-keys) | desconhecida | 2026-09-23 | alta |
| [32] | Function: Hobby 300 s, Pro 800 s, beta 1800 s | [Vercel](https://vercel.com/docs/functions/configuring-functions/duration) | desconhecida | 2026-09-23 | alta; relido |

## Mapa de validade

Calculado em 2026-09-23 com o script de staleness. Janelas: preço 3 meses, implementação 6, panorama 12, padrão 24. Página oficial sem data de publicação entra com a data da leitura.

Já vencidos, e por isso fora da conta do veredito: [9] (releitura 2026-08-15) e [12] (releitura 2026-07-01). [23] encosta na janela de implementação hoje (2026-09-23): o relato solo de Django está no limite; a contagem de meses até o MVP pede refresco antes de virar estimativa deste radar.

A releitura mais cedo do mapa inteiro é 2026-07-01, já passada, nesses preços descartados. A releitura mais cedo entre as afirmações que a escolha ainda usa é **2026-12-23**, nos preços lidos ao vivo [19][20][22].
