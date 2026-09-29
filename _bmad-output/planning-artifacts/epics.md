---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-rondimob-2026-09-23/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-rondimob-2026-09-23/ARCHITECTURE-SPINE.md
---

# rondimob - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for rondimob, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: O visitante vê, no mesmo site, os produtos, os planos e a entrada da área do cliente. Grátis é R$ 0 com 10 pesquisas em 14 dias. Padrão é R$ 97 por mês com 30 pesquisas. Plus é R$ 197 por mês com 100 pesquisas. Personalizado é sob consulta. O pacote de crédito é R$ 47 por 10 pesquisas.

FR2: Só corretor com CRECI ou imobiliária pessoa jurídica cria conta. A conferência desta versão é de formato, sem consulta ao conselho nem à Receita. A imobiliária informa razão social, CNPJ, responsável, e-mail e telefone. Os dois tipos veem a mesma área. A conta faz login, logout e recuperação de senha. A sessão vale até o logout e só para aquela conta.

FR3: Anúncio não tem dono de conta. Radar, favorito, alerta, crédito, visto do radar, envio e dados da conta são privados, com row-level security forçado. Uma conta não vê o que é de outra.

FR4: Sem plano pago, depois de 14 dias ou ao estourar as 10 pesquisas, a conta vê o nome dos radares e os planos, e não executa pesquisa, não favorita e não configura alerta. A cota do plano pago é do mês-calendário em America/Sao_Paulo e não acumula. Com cota esgotada, a conta vê resultados já gravados e não executa pesquisa nova.

FR5: A conta cria mais de um radar, em menos de 2 minutos, só no ABCD. O radar leva imobiliária anunciante, cidade, bairro, tipo, faixa de preço, faixa de área, quartos e vagas.

FR6: O sistema coleta ZAP Imóveis, Viva Real e OLX em filas separadas. A falha de uma fonte não cancela as outras. Preço, área, quartos, banheiros, vagas, bairro, cidade e tipo saem numa forma única. A meta é 95% das execuções sem erro crítico.

FR7: O anúncio novo e a mudança de preço aparecem no radar correspondente, com valor anterior, valor novo, diferença, percentual e data. A identidade é fonte mais identificador externo, ou a URL. Histórico de preço só ganha linha quando o preço muda.

FR8: A área do cliente mostra quantidade de novos, de quedas e de oportunidades, e a lista. Oportunidade é anúncio do radar que é novo ou teve redução de preço, sem score. A conta filtra e abre o anúncio original.

FR9: A conta favorita, desfavorita e vê só os próprios favoritos. A lista vazia aparece vazia. Do favorito, abre o anúncio original.

FR10: A conta escolhe aviso de novos e de redução de preço, e a frequência imediata, diária ou semanal. O padrão é diária. O mesmo anúncio e o mesmo fato entram no máximo uma vez na janela da frequência. O link abre o anúncio.

FR11: Conta com plano pago compra pacote de 10 pesquisas por R$ 47 sem mudar de plano. Só a conta altera cota e saldo. A cota é gasta antes do crédito. O crédito não vence nesta versão. A conta grátis não compra crédito.

### NonFunctional Requirements

NFR1: Criar um radar leva menos de 2 minutos.

NFR2: 95% das coletas terminam sem erro crítico.

NFR3: Cerca de 90% das contas encontram uma oportunidade relevante sem treinamento, no caminho abrir, filtrar, encontrar e abrir o anúncio.

NFR4: A sessão permanece autenticada até o logout e não serve para outra conta.

NFR5: O papel da web e o do worker não são superuser, não são donos das tabelas privadas e não têm BYPASSRLS. O contexto da conta é app.conta_id dentro da transação.

NFR6: A falha de uma fonte não derruba as outras nem o site.

NFR7: A interface não usa cor escura como base. O visual segue o padrão claro de SaaS imobiliário, com toque moderno. Não há preferência de tom. A paleta concreta fica com o UX.

NFR8: Preço e área são numeric. Área é em m². Quartos, banheiros e vagas são inteiros. Instante de coleta é timestamptz em UTC. Mês e prazo grátis usam America/Sao_Paulo.

### Additional Requirements

- Sem template inicial. Projeto greenfield.
- Python 3.13.15, Django 6.1.1, PostgreSQL 18.6, Celery 5.6.3, Redis 8.10.2.
- Um app web para portal público e área do cliente. Worker em processo separado. Um Postgres. Um Redis.
- Pastas: config, contas, anuncios, radares, coleta.
- anuncios é o dono de Anúncio e Preço. coleta entrega payload e não declara esses modelos.
- RadarVisto só é escrito numa pesquisa que contas já aceitou. A coleta para no corpus.
- Alerta é configuração. Envio é outro registro, escrito só pelo worker.
- Migração entra antes de a web e o worker novos atenderem. Backup é dump do Postgres. Log é a saída padrão dos dois processos.
- Nenhum módulo integra gateway de pagamento nesta versão. Ativar plano e somar crédito são mudança de estado em contas.
- Hospedeiro e fornecedor de e-mail continuam em aberto.
- Não há documento de UX. A direção visual entra só como NFR7.

### UX Design Requirements

Nenhum. O par DESIGN.md e EXPERIENCE.md não existe. UX-DR não foi extraído.

### FR Coverage Map

FR1: Epic 1 - Portal com planos e preços
FR2: Epic 1 - Cadastro, sessão e os dois tipos de conta
FR3: Epic 1 - Isolamento do que é de cada conta
FR4: Epic 1 - Grátis, bloqueio e cota do plano
FR5: Epic 2 - Criar radar no ABCD
FR6: Epic 3 - Coletar e normalizar as três fontes
FR7: Epic 3 - Anúncio novo e mudança de preço
FR8: Epic 3 - Ver oportunidades e abrir o anúncio
FR9: Epic 4 - Favoritar
FR10: Epic 4 - Receber e-mail
FR11: Epic 1 - Recarregar créditos sem mudar de plano

## Epic List

### Epic 1: Entrar e ter cota
O visitante vê os planos, cria a conta e usa o grátis. Depois ativa um plano ou recarrega créditos, e não vê os dados de outra conta.
**FRs covered:** FR1, FR2, FR3, FR4, FR11

### Epic 2: Definir o que monitorar
A conta cria um ou mais radares no ABCD, com os filtros do imóvel e da imobiliária anunciante, em menos de 2 minutos.
**FRs covered:** FR5

### Epic 3: Ver o que mudou no mercado
As fontes entram no corpus, e a conta vê, no radar, o anúncio novo e a queda de preço, e abre o anúncio original.
**FRs covered:** FR6, FR7, FR8

### Epic 4: Guardar e ser avisado
A conta favorita um imóvel e recebe o e-mail do radar, sem repetir o mesmo fato na janela da frequência.
**FRs covered:** FR9, FR10

## Epic 1: Entrar e ter cota

O visitante vê os planos, cria a conta e usa o grátis. Depois ativa um plano ou recarrega créditos, e não vê os dados de outra conta.

### Story 1.1: Ver produtos e planos no portal

As a visitante,
I want ver os produtos, os planos e a entrada da área do cliente no mesmo site,
So that eu saiba o que o rondimob faz e quanto custa antes de criar conta.

**Acceptance Criteria:**

**Given** que não existe conta autenticada
**When** o visitante abre o portal
**Then** ele vê os produtos do rondimob, os quatro planos e o pacote de crédito
**And** Grátis aparece a R$ 0, com 10 pesquisas em 14 dias; Padrão a R$ 97 por mês, com 30 pesquisas; Plus a R$ 197 por mês, com 100 pesquisas; Personalizado como sob consulta; o pacote a R$ 47 por 10 pesquisas

**Given** o mesmo site
**When** o visitante procura a área do cliente
**Then** encontra a entrada de login no portal público
**And** a base visual é clara, no padrão de SaaS imobiliário, sem tema escuro

**Given** o projeto ainda não existe
**When** esta história é implementada
**Then** nasce o app Django 6.1.1 em Python 3.13.15, com PostgreSQL 18.6, e as pastas config e contas
**And** a página pública não exige conta

### Story 1.2: Criar conta de corretor ou de imobiliária

As a visitante,
I want criar conta como corretor com CRECI ou como imobiliária pessoa jurídica,
So that só quem atua no mercado entre e os dois tipos caiam na mesma área.

**Acceptance Criteria:**

**Given** o portal público
**When** o visitante escolhe corretor e informa nome, e-mail, telefone, senha e CRECI no formato número mais UF
**Then** a conta de pessoa física é criada e ele entra na mesma área do cliente
**And** o CRECI é conferido só pelo formato, sem consulta ao conselho

**Given** o portal público
**When** o visitante escolhe imobiliária e informa razão social, CNPJ, responsável, e-mail, telefone e senha
**Then** a conta de pessoa jurídica é criada e ele vê a mesma área do corretor
**And** o CNPJ tem 14 dígitos e dígitos verificadores válidos, sem consulta à Receita

**Given** um CRECI sem UF, um CNPJ com dígito inválido, ou um cadastro sem o tipo
**When** o visitante envia o formulário
**Then** a conta não é criada e o campo inválido é indicado
**And** e-mail já usado também não cria outra conta

### Story 1.3: Entrar, sair e recuperar a senha

As a conta,
I want entrar com e-mail e senha, sair e recuperar a senha,
So that só eu acesse a minha área e eu volte a entrar se esquecer a senha.

**Acceptance Criteria:**

**Given** uma conta já criada
**When** a pessoa informa o e-mail e a senha corretos
**Then** a sessão abre a área daquela conta
**And** a sessão permanece até o logout

**Given** uma sessão aberta
**When** a conta sai
**Then** a área pede login de novo
**And** a sessão antiga não abre a conta de outra pessoa

**Given** e-mail ou senha incorretos
**When** a pessoa tenta entrar
**Then** a sessão não abre e a área privada continua fechada

**Given** uma conta que esqueceu a senha
**When** pede a recuperação
**Then** o pedido sai do request e vira tarefa do worker, sem fornecedor de e-mail escolhido nesta história
**And** o link define uma senha nova e a senha antiga deixa de entrar

### Story 1.4: Uma conta não lê a outra

As a conta,
I want ver só os meus dados,
So that o cadastro de outra conta não apareça para mim.

**Acceptance Criteria:**

**Given** duas contas já criadas
**When** a conta A abre uma transação
**Then** ela lê e altera só os próprios dados
**And** a consulta não devolve linha da conta B

**Given** um acesso a dado privado da conta
**When** a transação começa
**Then** o código chama `set_config('app.conta_id', ..., true)` antes das queries
**And** o valor acaba com a transação e não vaza para o próximo request

**Given** os papéis da web e do worker
**When** eles conectam no Postgres
**Then** não são superuser, não são donos das tabelas privadas e não têm `BYPASSRLS`
**And** os dados da conta usam `ENABLE` e `FORCE ROW LEVEL SECURITY`, num schema só, sem django-tenants

**Given** radar, favorito, alerta, crédito, visto do radar e envio ainda não existem
**When** esta história termina
**Then** só a tabela de dados da conta recebe a policy
**And** cada tabela privada futura nasce com a mesma `FORCE ROW LEVEL SECURITY` na história que a cria

### Story 1.5: Usar o grátis e ver o bloqueio

As a conta,
I want usar 10 pesquisas nos primeiros 14 dias e, depois disso, ver o pedido de plano,
So that eu experimente o produto e saiba quando a conta deixa de pesquisar.

**Acceptance Criteria:**

**Given** uma conta recém-criada, sem plano pago
**When** ela entra na área
**Then** o grátis vale 14 dias-calendário a partir da data de criação, em America/Sao_Paulo, com no máximo 10 pesquisas
**And** só `contas` altera esse contador

**Given** a conta ainda no prazo e com pesquisas restantes
**When** uma pesquisa é aceita
**Then** o contador diminui um
**And** criar conta, entrar na área e abrir a página de planos não gastam pesquisa

**Given** o 15º dia sem plano pago, ou as 10 pesquisas já usadas
**When** a conta entra
**Then** ela vê os nomes dos radares que já existirem e os planos
**And** a conta não executa pesquisa, não favorita e não configura alerta

**Given** pesquisa, favorito e alerta ainda não têm tela própria
**When** esta história termina
**Then** existe o portão em `contas` que as histórias futuras consultam antes dessas ações
**And** a cota do plano pago fica para a história de ativar o plano

### Story 1.6: Ativar plano pago

As a conta,
I want ativar Padrão ou Plus,
So that eu volte a pesquisar com a cota do mês, sem um gateway de pagamento nesta versão.

**Acceptance Criteria:**

**Given** uma conta autenticada
**When** ela ativa Padrão
**Then** `contas` grava o plano e a cota de 30 pesquisas no mês-calendário de America/Sao_Paulo
**And** nenhum módulo chama Mercado Pago, Stripe ou outro gateway

**Given** uma conta autenticada
**When** ela ativa Plus
**Then** a cota do mês passa a 100 pesquisas
**And** as funções de monitoramento são as mesmas do Padrão

**Given** o plano Personalizado
**When** a conta o consulta
**Then** o produto pede contato e não grava cota nem ativa o plano

**Given** um plano pago ativo
**When** o mês-calendário vira
**Then** a cota recomeça em 30 ou 100, conforme o plano
**And** o que sobrou no mês anterior não acumula

**Given** plano pago com cota do mês em zero e sem crédito
**When** a conta entra
**Then** ela vê os resultados já gravados
**And** uma pesquisa nova não é aceita

### Story 1.7: Recarregar créditos

As a conta com plano pago,
I want somar 10 pesquisas por R$ 47 sem mudar de plano,
So that eu continue pesquisando quando a cota do mês acabar.

**Acceptance Criteria:**

**Given** uma conta Padrão ou Plus
**When** ela recarrega um pacote
**Then** o saldo da conta aumenta 10, o plano permanece o mesmo e o preço registrado é R$ 47
**And** a recarga é mudança de estado em `contas`, no request web, sem gateway e sem executar pesquisa

**Given** cota do mês ainda disponível e saldo de crédito maior que zero
**When** uma pesquisa é aceita
**Then** a cota diminui um e o saldo de crédito permanece
**And** o crédito só diminui depois que a cota do mês chega a zero

**Given** cota do mês em zero e saldo de crédito maior que zero
**When** uma pesquisa é aceita
**Then** o saldo diminui um e a pesquisa segue
**And** o crédito comprado não zera na virada do mês

**Given** uma conta grátis
**When** ela tenta recarregar
**Then** o saldo não muda
**And** o produto pede ativação de plano

**Given** a tabela de crédito criada nesta história
**When** a conta A consulta o saldo
**Then** ela não vê o saldo da conta B
**And** a tabela usa `ENABLE` e `FORCE ROW LEVEL SECURITY`, e o identificador exposto é UUID

## Epic 2: Definir o que monitorar

A conta cria um ou mais radares no ABCD, com os filtros do imóvel e da imobiliária anunciante, em menos de 2 minutos.

### Story 2.1: Criar radares no ABCD

As a conta,
I want criar mais de um radar no ABCD,
So that eu monitore a região e a imobiliária anunciante que me interessam.

**Acceptance Criteria:**

**Given** uma conta autenticada
**When** ela preenche um único formulário com imobiliária anunciante, cidade, bairro, tipo, faixa de preço, faixa de área, quartos mínimos e vagas mínimas
**Then** o radar é salvo na conta e aparece na lista dela
**And** o fluxo não tem etapa além desse formulário

**Given** o exemplo Santo André, apartamento, R$ 300.000 a R$ 800.000, 2 quartos ou mais, 60 m² ou mais, 1 vaga ou mais e uma imobiliária anunciante
**When** a conta salva
**Then** o radar guarda esses filtros
**And** cidade só aceita Santo André, São Bernardo do Campo, São Caetano do Sul ou Diadema

**Given** uma cidade fora do ABCD
**When** a conta tenta salvar
**Then** o radar não é criado

**Given** uma conta que já tem um radar
**When** ela cria outro
**Then** os dois permanecem na lista
**And** criar radar não gasta pesquisa

**Given** a tabela de radar criada nesta história
**When** a conta A lista os radares
**Then** ela não vê radar da conta B
**And** a tabela usa `ENABLE` e `FORCE ROW LEVEL SECURITY`, e o identificador exposto é UUID

### Story 2.2: Editar radar

As a conta,
I want corrigir os filtros de um radar que já existe,
So that eu ajuste o monitoramento sem perder o radar e sem gastar pesquisa.

**Acceptance Criteria:**

**Given** um radar da conta
**When** ela altera bairro, tipo, faixa de preço, faixa de área, quartos, vagas ou imobiliária anunciante e salva
**Then** o mesmo radar fica com os filtros novos
**And** a edição não cria outro radar e não gasta pesquisa

**Given** uma cidade fora do ABCD
**When** a conta tenta salvar a edição
**Then** o radar permanece com a cidade anterior

**Given** o radar da conta B
**When** a conta A tenta editá-lo
**Then** o radar da conta B não muda

## Epic 3: Ver o que mudou no mercado

As fontes entram no corpus, e a conta vê, no radar, o anúncio novo e a queda de preço, e abre o anúncio original.

### Story 3.1: Coletar o ZAP e gravar o anúncio

As a conta,
I want que os anúncios do ZAP Imóveis entrem num corpus único,
So that a pesquisa compare o mercado já gravado, e não uma página buscada na hora.

**Acceptance Criteria:**

**Given** o worker separado da web
**When** a coleta do ZAP roda
**Then** ela usa a fila do ZAP, Celery 5.6.3 e Redis 8.10.2, e não roda dentro do request HTTP
**And** a migração entra antes de a web e o worker novos atenderem, o log sai em stdout e o worker é um processo separado

**Given** um payload do ZAP
**When** o worker grava
**Then** `anuncios` é o dono de Anúncio e Preço, e `coleta` só entrega o payload
**And** preço e área são `numeric`, área em m²; quartos, banheiros e vagas são inteiros; cidade, bairro, tipo e imobiliária anunciante são texto normalizado; o instante da coleta é `timestamptz` em UTC

**Given** os textos "R$ 650.000", "650 mil" e "650000"
**When** o worker grava o preço
**Then** os três viram o mesmo `numeric`

**Given** um anúncio já gravado com o mesmo preço
**When** a coleta se repete
**Then** não nasce outro anúncio nem outra linha de preço, e o instante da coleta é atualizado
**And** a chave é fonte mais identificador externo quando ele é confiável; sem isso, a chave é a URL

**Given** o mesmo anúncio com preço numérico diferente
**When** a coleta grava
**Then** nasce uma linha de Preço com o valor novo

**Given** a coleta do ZAP
**When** ela termina ou falha
**Then** nenhuma conta é debitada e `RadarVisto` não é escrito
**And** a falha fica registrada

### Story 3.2: Coletar a Viva Real sem parar o resto

As a conta,
I want a Viva Real na fila dela,
So that uma falha do ZAP não apague essa fonte nem derrube o site.

**Acceptance Criteria:**

**Given** a fila da Viva Real
**When** a coleta roda
**Then** o payload segue o mesmo contrato e o mesmo upsert de `anuncios` da história 3.1
**And** a coleta não roda dentro do request HTTP

**Given** uma falha na fila do ZAP
**When** a fila da Viva Real executa
**Then** a Viva Real conclui ou registra o próprio erro
**And** o site continua respondendo

### Story 3.3: Coletar a OLX sem parar o resto

As a conta,
I want a OLX na fila dela,
So that as três fontes existam e a falha de uma não cancele as outras.

**Acceptance Criteria:**

**Given** a fila da OLX
**When** a coleta roda
**Then** o payload segue o mesmo contrato e o mesmo upsert de `anuncios`
**And** a coleta não roda dentro do request HTTP

**Given** uma falha na Viva Real ou no ZAP
**When** a fila da OLX executa
**Then** a OLX conclui ou registra o próprio erro
**And** as outras filas e o site seguem

### Story 3.4: Ver o que é novo e o que mudou de preço

As a conta,
I want executar um radar contra o corpus e ver o anúncio novo e a mudança de preço,
So that eu encontre a oportunidade sem receber o mesmo fato de novo.

**Acceptance Criteria:**

**Given** um radar da conta e anúncios no corpus que cabem nos filtros
**When** a conta executa a pesquisa e `contas` aceita
**Then** a pesquisa compara só as colunas do contrato e gasta uma pesquisa
**And** `RadarVisto` grava radar, anúncio, fato e instante só depois dessa aceitação, com `ENABLE` e `FORCE ROW LEVEL SECURITY`

**Given** um anúncio que o radar ainda não tinha visto
**When** a pesquisa aceita roda
**Then** ele aparece uma vez como novo
**And** uma pesquisa seguinte não o marca de novo

**Given** um anúncio do radar cujo preço numérico mudou
**When** a pesquisa aceita roda
**Then** a conta vê valor anterior, valor novo, diferença, percentual e data
**And** diferença é valor novo menos valor anterior, e percentual é essa diferença sobre o valor anterior

**Given** o portão de `contas` recusa a pesquisa
**When** a conta tenta executar
**Then** `RadarVisto` não é escrito e a cota não muda outra vez

**Given** um resultado já gravado
**When** a conta abre de novo
**Then** a abertura não gasta pesquisa

### Story 3.5: Abrir, filtrar e achar a oportunidade

As a conta,
I want ver quantos anúncios são novos, quantos caíram de preço e abrir o anúncio,
So that eu ache uma oportunidade em poucos cliques, sem score e sem treinamento.

**Acceptance Criteria:**

**Given** pesquisas já aceitas
**When** a conta abre a área
**Then** a tela mostra a quantidade de novos, a quantidade de quedas de preço, a quantidade de oportunidades e a lista
**And** oportunidade é anúncio do radar que é novo ou teve redução de preço, e não é score

**Given** a lista
**When** a conta filtra por radar, bairro, preço, tipo, quartos, área, somente novos ou somente redução de preço
**Then** a lista mostra só o que passou no filtro
**And** o caminho é abrir, filtrar, encontrar e abrir o anúncio original

**Given** uma conta sem oportunidades
**When** ela abre a área
**Then** as quantidades são zero e a lista aparece vazia

**Given** plano pago com cota esgotada e resultados já gravados
**When** a conta abre a área
**Then** ela vê esses resultados e não executa pesquisa nova

## Epic 4: Guardar e ser avisado

A conta favorita um imóvel e recebe o e-mail do radar, sem repetir o mesmo fato na janela da frequência.

### Story 4.1: Favoritar o imóvel

As a conta,
I want guardar e tirar um imóvel dos favoritos,
So that eu volte nele e abra o anúncio original.

**Acceptance Criteria:**

**Given** um anúncio visível para a conta e o portão de `contas` permitindo favoritar
**When** ela favorita
**Then** o favorito aponta para a chave primária do anúncio e permanece até ela desfavoritar
**And** a tabela usa `ENABLE` e `FORCE ROW LEVEL SECURITY`, e o identificador exposto é UUID

**Given** favoritos da própria conta
**When** ela abre a lista
**Then** vê só os seus e, a partir de um item, abre o anúncio original

**Given** nenhum favorito
**When** ela abre a lista
**Then** a lista aparece vazia

**Given** o portão recusando favoritar, ou o favorito da conta B
**When** a conta A tenta favoritar ou listar
**Then** o favorito não é criado para A e a lista de B não aparece

### Story 4.2: Configurar o aviso

As a conta,
I want escolher se o e-mail traz novos e redução de preço, e com que frequência,
So that o aviso acompanhe o radar sem eu abrir o sistema todo dia.

**Acceptance Criteria:**

**Given** uma conta autenticada e o portão permitindo configurar alerta
**When** ela abre a configuração
**Then** aviso de novos e aviso de redução de preço começam ligados, e a frequência mostrada é diária
**And** `Alerta` é configuração da conta, dono `radares`, gravado só na área autenticada

**Given** a configuração
**When** ela desliga um dos avisos ou escolhe imediata, diária ou semanal
**Then** a escolha fica salva na conta
**And** a configuração não grava `Envio`

**Given** o portão recusando a configuração, ou o alerta da conta B
**When** a conta A tenta alterar
**Then** a configuração não muda
**And** a tabela usa `ENABLE` e `FORCE ROW LEVEL SECURITY`

### Story 4.3: Receber o e-mail uma vez

As a conta,
I want receber o e-mail do fato uma única vez,
So that eu abra o anúncio sem receber o mesmo aviso de novo.

**Acceptance Criteria:**

**Given** um alerta salvo e um fato novo ou de redução de preço ainda não enviado
**When** chega a hora da frequência
**Then** o worker, e não o request web, grava `Envio` e produz a mensagem com o link do anúncio original
**And** nenhum fornecedor de e-mail é escolhido nesta história

**Given** frequência diária ou semanal
**When** o mesmo anúncio e o mesmo fato já estão no `Envio`
**Then** o período seguinte não envia esse par de novo
**And** uma redução de preço diferente é outro fato e pode ser enviada uma vez

**Given** frequência imediata
**When** o fato nasce numa pesquisa já aceita
**Then** a mensagem sai uma vez para esse anúncio e esse fato

**Given** os dois avisos desligados, ou a conta B
**When** o worker processa
**Then** a conta não recebe mensagem do que desligou e não vê o `Envio` da outra conta
**And** `Envio` pertence a `coleta`, usa `ENABLE` e `FORCE ROW LEVEL SECURITY`, e o worker abre uma transação por conta

**Given** falha ao produzir a mensagem
**When** o worker registra o erro
**Then** o site continua respondendo e as outras contas seguem
