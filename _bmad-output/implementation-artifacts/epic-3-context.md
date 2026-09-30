# Epic 3 Context: Ver o que mudou no mercado

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

As três fontes entram num corpus único, e a conta autenticada executa o radar contra o que já está gravado: vê o anúncio novo e a mudança de preço, e abre o anúncio original. A coleta não é pesquisa e não gasta cota. Este épico é o monitoramento; favorito e e-mail ficam no épico seguinte. Não há score.

## Stories

- Story 3.1: Coletar o ZAP e gravar o anúncio
- Story 3.2: Coletar a Viva Real sem parar o resto
- Story 3.3: Coletar a OLX sem parar o resto
- Story 3.4: Ver o que é novo e o que mudou de preço
- Story 3.5: Abrir, filtrar e achar a oportunidade

## Requirements & Constraints

Fontes desta versão: ZAP Imóveis, Viva Real e OLX. Cada uma é coletada sozinha. A falha de uma fica registrada e não cancela as outras nem derruba o site. A barra de sucesso da coleta é 95% das execuções sem erro crítico, com 1.000 anúncios ou mais monitorados.

O anúncio mínimo traz título, URL, preço, tipo, endereço ou região, bairro, cidade, área, quartos, banheiros, vagas, descrição, imobiliária anunciante, instante da coleta e fonte. Preço, área, quartos, banheiros, vagas, bairro, cidade e tipo saem numa forma única. "R$ 650.000", "650 mil" e "650000" são o mesmo preço. Duplicata não vira outro anúncio. O histórico de preço se reconstrói: nova linha só quando o preço numérico muda.

Pesquisa é uma execução de um radar da conta contra o corpus já gravado. Compara só as colunas do contrato do anúncio com os filtros do radar. Gasta uma pesquisa somente se `contas` aceita. Abrir um resultado já gravado não gasta de novo. Sem plano, a conta não executa pesquisa. Com plano e cota esgotada, vê os resultados já gravados e não executa pesquisa nova.

Novo, para aquele radar, é o anúncio que ele ainda não tinha visto, e aparece uma vez. Mudança de preço mostra valor anterior, valor novo, diferença, percentual e data. Diferença é valor novo menos valor anterior; percentual é essa diferença sobre o valor anterior. Oportunidade é anúncio do radar que é novo ou teve redução de preço. Alta de preço entra no histórico e na mudança, e não conta como oportunidade nem como queda.

A área mostra a quantidade de novos, a quantidade de quedas de preço, a quantidade de oportunidades e a lista. Dá para filtrar por radar, bairro, preço, tipo, quartos, área, somente novos ou somente redução de preço. O caminho é abrir, filtrar, encontrar e abrir o anúncio original. Sem oportunidades, as quantidades são zero e a lista aparece vazia. Cerca de 90% das contas devem achar uma oportunidade relevante sem treinamento. O anúncio novo e a mudança de preço têm de aparecer corretos no radar correspondente.

O corpus é o mesmo para todas as contas. O visto de cada radar é privado.

## Technical Decisions

A web atende a área do cliente e não coleta dentro do request HTTP. O worker é outro processo, supervisionado, com Celery 5.6.3 e Redis 8.10.2. Cada fonte tem a própria fila. O worker não renderiza página. O log dos dois processos é stdout. A migração entra antes de a web e o worker novos atenderem. Em volta: Python 3.13.15, Django 6.1.1, PostgreSQL 18.6. Um Postgres, um Redis, um schema. django-tenants não entra.

`coleta` entrega o payload e não declara os modelos. `anuncios` é o dono de Anúncio e Preço. Só o upsert do worker grava as colunas. Preço e área são `numeric`, área em m². Quartos, banheiros e vagas são inteiros. Cidade, bairro, tipo e imobiliária anunciante são texto já normalizado. O instante da coleta é `timestamptz` em UTC. A chave única é fonte mais identificador externo quando ele é confiável; sem isso, a chave é a URL. Coleta que repete o preço atual só atualiza o instante. Uma linha de Preço nasce quando o `numeric` muda. Anúncio não tem dono de conta.

`RadarVisto` guarda radar, anúncio, fato e instante. Mora em `radares`, é privado, e usa `ENABLE` e `FORCE ROW LEVEL SECURITY`. Só é escrito dentro de uma pesquisa que `contas` já aceitou. Se o portão recusa, `RadarVisto` não é escrito e a cota não muda outra vez. A coleta para no corpus. Os papéis da web e do worker não são superuser, não são donos das tabelas privadas e não têm `BYPASSRLS`. Dentro da transação, antes das queries privadas, `set_config('app.conta_id', ..., true)`. A policy lê `app.conta_id`. O valor morre com a transação. O worker que cruza contas lê os identificadores e abre uma transação por conta.

## UX & Interaction Patterns

Não há documento de UX. A área do cliente é enxuta, no mesmo site, com fundo claro: cor escura não é a base. O visual segue o padrão de SaaS imobiliário, mais moderno e menos rígido. Paleta e biblioteca de interface ficam em aberto.

A tela inicial junta as três quantidades e a lista. O passo seguinte é filtrar e abrir o anúncio original, em poucos cliques, sem score e sem treinamento.

## Cross-Story Dependencies

As três coletas compartilham o mesmo contrato de payload e o mesmo upsert. A fila de uma fonte não espera nem cancela a das outras. A pesquisa só roda com o corpus gravado e com os radares do épico 2, e só grava o visto depois que o portão de cota do épico 1 aceita. A tela lê pesquisas já aceitas; reabrir não dispara outra pesquisa.

O épico 4 favorita pela chave primária do anúncio e avisa os mesmos fatos (novo e redução de preço). Este épico não grava favorito nem envio.
