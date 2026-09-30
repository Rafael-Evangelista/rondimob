# Epic 2 Context: Definir o que monitorar

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A conta autenticada define o que quer acompanhar: um ou mais radares no ABCD, com os filtros do imóvel e da imobiliária anunciante, num único formulário que cabe em menos de 2 minutos. O radar fica na conta e pode ser corrigido sem virar outro radar e sem gastar pesquisa. Este épico entrega a definição do monitoramento; a coleta, a lista de oportunidades e o aviso ficam para os épicos seguintes.

## Stories

- Story 2.1: Criar radares no ABCD
- Story 2.2: Editar radar

## Requirements & Constraints

Radar é o conjunto de filtros do que a conta quer monitorar. Uma conta pode ter mais de um, e todos permanecem na lista dela. O filtro de imobiliária anunciante serve para analisar concorrentes. Corretor e imobiliária usam a mesma área.

O fluxo de criação é um único formulário, sem etapa extra. Os campos são imobiliária anunciante, cidade, bairro, tipo do imóvel, faixa de preço, faixa de área, quartos mínimos e vagas mínimas. Banheiros não entram no radar. O exemplo que tem de caber: Santo André, apartamento, R$ 300.000 a R$ 800.000, 2 quartos ou mais, 60 m² ou mais, 1 vaga ou mais, e uma imobiliária anunciante.

Cidade só aceita o ABCD: Santo André, São Bernardo do Campo, São Caetano do Sul e Diadema. Fora disso o radar não é criado. Na edição, cidade fora do ABCD não grava: o radar permanece com a cidade anterior. Editar bairro, tipo, faixa de preço, faixa de área, quartos, vagas, imobiliária anunciante ou cidade (dentro do ABCD) atualiza o mesmo radar; não cria outro.

Criar e editar radar não gastam pesquisa e não disparam pesquisa. Pesquisa é a execução de um radar contra o corpus já gravado, e não faz parte deste épico. Sem plano, depois do grátis, a conta ainda vê o nome dos radares já criados; o que fica bloqueado é executar pesquisa, favoritar e configurar alerta.

A lista e a edição são da conta dona. A conta A não vê nem altera radar da conta B.

Sucesso deste épico: o radar nasce em menos de 2 minutos.

## Technical Decisions

O radar mora em `radares`. A mutação só acontece na área autenticada, sob a conta da transação. A tabela usa `ENABLE` e `FORCE ROW LEVEL SECURITY`. Os papéis da web e do worker não são superuser, não são donos da tabela e não têm `BYPASSRLS`. Dentro da transação, antes das queries, o código chama `set_config('app.conta_id', ..., true)`. A policy lê `app.conta_id`. O valor morre com a transação. Um schema só; django-tenants não entra. O identificador exposto do radar é UUID.

O filtro tem de comparar o contrato do anúncio, mesmo que o corpus ainda não exista: preço e área são `numeric` (área em m²); quartos e vagas são inteiros; cidade, bairro, tipo e imobiliária anunciante são texto já normalizado. Anúncio não tem dono de conta. Radar aponta para a conta, não para o anúncio.

A migração entra antes de a web e o worker novos atenderem.

## UX & Interaction Patterns

Não há documento de UX. A área do cliente é enxuta, no mesmo site do portal, com fundo claro: cor escura não é a base. O visual segue o padrão de SaaS imobiliário, mais moderno e menos rígido. A paleta concreta e a biblioteca de interface ficam em aberto.

Criar o radar é um formulário só, reconhecível em menos de 2 minutos, sem assistente de etapas.

## Cross-Story Dependencies

Depende da conta autenticada e do padrão de isolamento do épico 1: a policy de `app.conta_id` se repete na tabela de radar. O portão de cota em `contas` não é debitado aqui; criar e editar passam sem pesquisa. A lista de nomes precisa existir para o bloqueio do épico 1 mostrar os radares já criados.

A edição usa o radar gravado na criação. O épico 3 compara esses filtros com o corpus e grava o visto do radar só dentro de uma pesquisa aceita por `contas`. Favorito e alerta, no épico 4, também moram em `radares` e apontam para o radar, com a mesma política de linha.
