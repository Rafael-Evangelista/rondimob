---
title: rondimob
status: final
created: 2026-09-23
updated: 2026-09-29
---

# PRD: rondimob

*Documento final em 2026-09-23. Seis perguntas seguem adiadas e não impedem este fecho.*

## 0. Para quem é este documento

Este PRD é para quem vai desenhar a experiência, a arquitetura e as histórias do rondimob. O vocabulário está no glossário. As jornadas são as cenas confirmadas. O comportamento que o usuário mandou seguir está em `MVP/mvp.md`. A stack e a ambição de RAG e fine tuning estão no `addendum.md`, fora daqui.

## 1. Visão

O rondimob é o lugar único em que o corretor e a imobiliária acompanham preço por região e concorrentes no ABCD. A promessa desta versão é: monitorar o mercado e avisar quando aparece algo relevante.

A ideia nasceu com o Rafael e um chat de IA, da vontade de fazer algo útil com scraping, RAG e fine tuning. O que está em prática nesta versão é o monitoramento. RAG e fine tuning ficam para depois.

Se o resultado não for o esperado, o produto se ajusta.

## 2. Quem usa

### 2.1 O que a pessoa quer fazer

- Acompanhar preço por região e os concorrentes sem abrir cada portal.
- Saber o que é novo e o que baixou de preço desde a última coleta.
- Fazer isso numa área enxuta, fácil de achar, com login e senha.

### 2.2 Quem fica de fora nesta versão

- Quem não é corretor com CRECI e não é imobiliária em cadastro de pessoa jurídica.
- Comprador e investidor pessoa física.
- Quem espera CRM, aplicativo ou conversa com inteligência artificial.

### 2.3 Jornadas

#### UJ-1. Vinicius cria a conta, monta um radar em Santo André e acompanha o mercado do ABCD.

- **Persona + contexto:** Vinicius, corretor. Quer uma área do cliente enxuta e simples.
- **Estado de entrada:** está no site público. A entrada da área do cliente é óbvia, porque o acesso pede login e senha.
- **Caminho:**
  1. Vinicius se cadastra como corretor, com CRECI. Conta de pessoa física. Os primeiros 14 dias são grátis, com no máximo 10 pesquisas nesse período. Depois, é preciso ativar um plano. Quem não é corretor com CRECI, nem imobiliária com cadastro de pessoa jurídica, não cria conta.
  2. Vinicius entra na área do cliente. A imobiliária, em cadastro de pessoa jurídica, vê a mesma área. Nesta versão, o que muda entre os dois é o cadastro, não a visão.
  3. O monitoramento cobre só o ABCD: Santo André, São Bernardo do Campo, São Caetano do Sul e Diadema. Ele cria um radar com imobiliária, região Santo André, tipo apartamento, preço de R$ 300.000 a R$ 800.000, 2 quartos ou mais, 60 m² ou mais e 1 vaga ou mais. O filtro de imobiliária serve para analisar concorrentes.
  4. Dashboard, favoritos e e-mail seguem FR-8, FR-9 e FR-10.
- **Clímax:** Vinicius vê, num lugar só, o preço por região e os concorrentes.
- **Resolução:** ele fica na área do cliente, com o radar de Santo André pronto.
- **Borda:** no 15º dia o grátis acaba. Continuação na UJ-2.

**Confirmação:** confirmada em 2026-09-23.

#### UJ-2. O grátis acaba e a área pede um plano.

- **Persona + contexto:** Vinicius no 15º dia. A mesma cena vale para a imobiliária.
- **Estado de entrada:** a conta e o radar existem. Os 14 dias terminaram. Nenhum plano pago está ativo.
- **Caminho:** as funções são bloqueadas. O produto pede a ativação de um plano. Os planos são grátis de 14 dias, padrão, plus e personalizado. Padrão e plus ainda não têm valor. O personalizado pede contato. A diferença entre o que cada plano libera não foi definida.
- **Clímax:** para voltar a monitorar, é preciso ativar um plano.
- **Resolução:** sem plano ativo, as funções seguem bloqueadas.
- **Borda:** sem plano, ele ainda entra, vê o nome dos radares que já criou e a página de planos, e não roda pesquisa nova. Com plano e cota esgotada, ele vê os resultados já gerados e pode recarregar créditos.

## 3. Glossário

- **Corretor** — pessoa física com CRECI que pode criar conta. Vê a mesma área do cliente que a imobiliária.
- **Imobiliária** — pessoa jurídica que pode criar conta. Vê a mesma área do cliente que o corretor.
- **Área do cliente** — parte autenticada do portal. Login e senha. Enxuta.
- **Portal público** — parte aberta do mesmo site, com os produtos e os planos.
- **Radar** — conjunto de filtros do que a conta quer monitorar. Uma conta pode ter mais de um.
- **Alerta** — aviso por e-mail que a conta configura. Não é um objeto separado do e-mail.
- **Oportunidade** — anúncio que casa com o radar e é novo ou teve redução de preço. Nesta versão não há score.
- **ABCD** — Santo André, São Bernardo do Campo, São Caetano do Sul e Diadema.
- **Pesquisa** — uma execução de um radar da conta contra o corpus já coletado. A coleta das fontes não é pesquisa e não gasta cota. Criar ou editar o radar não gasta. Abrir um resultado já gerado não gasta de novo.
- **Crédito** — pesquisas compradas à parte, somadas à conta, sem mudar o plano. A cota do plano é usada primeiro. O crédito entra quando a cota do período acaba.
- **Plano** — grátis, padrão, plus ou personalizado. As funções são as mesmas. O que muda é a quantidade de pesquisas incluída. O valor em reais segue em aberto.
- **Fonte** — site de anúncios de onde a coleta lê. Uma fonte que falha não derruba as outras.

## 4. Funcionalidades

### 4.1 Portal público

**Descrição:** Qualquer visitante vê os produtos e os planos no mesmo site em que está a área do cliente. Realiza o começo da UJ-1.

#### FR-1: Ver produtos e planos sem conta

O visitante vê, no portal público, os produtos do rondimob e os quatro planos: grátis de 14 dias, padrão, plus e personalizado.

**Consequências:**

- Padrão aparece a R$ 97 por mês. Plus aparece a R$ 197 por mês. O pacote de 10 créditos aparece a R$ 47.
- Personalizado oferece contato para valores.
- A entrada da área do cliente está visível e pede login e senha.

### 4.2 Conta

**Descrição:** Só corretor com CRECI ou imobiliária pessoa jurídica cria conta. Os dois veem a mesma área. Realiza UJ-1 e UJ-2.

#### FR-2: Criar conta de corretor ou de imobiliária

O visitante cria uma conta de corretor, com CRECI, ou de imobiliária, como pessoa jurídica.

**Consequências:**

- Os dois tipos entram na mesma área do cliente.
- Quem não se enquadra não conclui o cadastro.
- `[ASSUMPTION: nesta versão o CRECI e o CNPJ são informados pela pessoa e conferidos no formato. Não há consulta ao conselho nem à Receita.]`
- A imobiliária informa razão social, CNPJ, nome de quem responde, e-mail e telefone.
- A conta faz login, logout e recuperação de senha.
- A sessão permanece autenticada até o logout e não serve para outra conta.

**Fora deste requisito:** login social, SSO e vários níveis de permissão.

#### FR-3: Isolar o que é de cada conta

Uma conta não vê radar, favorito, alerta nem configuração de outra.

**Consequências:**

- O que o Vinicius configurou não aparece na conta da imobiliária ao lado.
- Os anúncios do mercado monitorado são o mesmo corpus para as contas. O que é privado é a configuração e o uso de cada uma.

#### FR-4: Encerrar o grátis e bloquear

Ao fim de 14 dias, sem plano pago, as funções que gastam pesquisa bloqueiam e o produto pede ativação de plano. Durante os 14 dias, a conta faz no máximo 10 pesquisas. No plano pago, a conta gasta a cota do período e, se precisar de mais, recarrega créditos sem mudar de plano.

**Consequências:**

- No 15º dia, sem plano ativo, a conta entra, vê o nome dos radares já criados e os planos, e não executa pesquisa, não favorita e não configura alerta.
- A 11ª pesquisa no período grátis não é aceita.
- Padrão inclui 30 pesquisas por mês, por R$ 97.
- Plus inclui 100 pesquisas por mês, por R$ 197.
- Personalizado combina a quantidade e o valor no contato.
- A cota do plano zera no fim do período e não acumula.
- Com plano ativo e cota esgotada, a conta vê os resultados já gerados e não executa pesquisa nova até recarregar créditos ou até a cota renovar.
- Corretor e imobiliária recarregam créditos do mesmo jeito.

#### FR-11: Recarregar créditos

A conta com plano pago compra pesquisas avulsas sem trocar de plano.

**Consequências:**

- O crédito entra na conta, não no plano.
- A execução usa primeiro a cota do plano e depois o crédito.
- O pacote é de 10 pesquisas, por R$ 47.
- O crédito comprado não vence nesta versão.
- A conta grátis não compra crédito. Ela ativa um plano.

### 4.3 Radar

**Descrição:** A conta define o que monitorar, em menos de 2 minutos, e pode ter mais de um radar. Realiza UJ-1.

#### FR-5: Criar radar no ABCD

A conta cria um radar com imobiliária anunciante, cidade do ABCD, bairro, tipo do imóvel, faixa de preço, faixa de área, quartos e vagas.

**Consequências:**

- Fora do ABCD, o radar não é criado nesta versão.
- O exemplo narrado cabe: Santo André, apartamento, R$ 300.000 a R$ 800.000, 2 quartos ou mais, 60 m² ou mais, 1 vaga ou mais, e uma imobiliária anunciante.
- A conta cria mais de um radar.

### 4.4 Monitoramento

**Descrição:** O sistema coleta anúncios das fontes escolhidas, normaliza, e mostra o que é novo e o que mudou de preço. Realiza o clímax da UJ-1.

#### FR-6: Coletar e normalizar anúncios

Cada fonte suportada é coletada sozinha. Preço, área, quartos, banheiros, vagas, bairro, cidade e tipo do imóvel saem numa forma única.

**Consequências:**

- A falha de uma fonte não interrompe as outras.
- "R$ 650.000", "650 mil" e "650000" viram o mesmo preço.
- Duplicata da mesma coleta não vira outro anúncio.
- Erro de coleta fica registrado.
- Meta do MVP: 95% das execuções sem erro crítico. As primeiras fontes são ZAP Imóveis, Viva Real e OLX.

**Dados mínimos do anúncio:** título, URL, preço, tipo, endereço ou região, bairro, cidade, área, quartos, banheiros, vagas, descrição, imobiliária anunciante, data da coleta e fonte.

#### FR-7: Apontar anúncio novo e mudança de preço

A conta vê, no radar correspondente, o anúncio que não estava na coleta anterior e a mudança de preço, com valor anterior, valor novo, diferença, percentual e data.

**Consequências:**

- O anúncio novo aparece uma vez, não a cada execução.
- A identificação prefere a fonte mais o identificador externo. Sem identificador confiável, usa a URL.
- A sequência de preços dos anúncios monitorados pode ser reconstruída.

### 4.5 Área do cliente

**Descrição:** A tela inicial mostra o que mudou e leva ao anúncio em poucos cliques. Realiza UJ-1.

#### FR-8: Ver oportunidades e abrir o anúncio

A conta abre a área, filtra e abre o anúncio original.

**Consequências:**

- A tela inicial mostra a quantidade de novos, a quantidade de quedas de preço e a quantidade de oportunidades, e a lista. Oportunidade é o anúncio do radar que é novo ou teve redução de preço. Não é score.
- Dá para filtrar por radar, bairro, preço, tipo, quartos, área, somente novos e somente redução de preço.
- O caminho é abrir, filtrar, encontrar, abrir o anúncio.

#### FR-9: Favoritar

A conta favorita, desfavorita, vê a lista de favoritos e abre o anúncio original a partir dela.

**Consequências:**

- O favorito permanece na conta até ela desfavoritar.
- A lista de uma conta não aparece em outra.
- A partir do favorito, a conta abre o anúncio original.
- Sem favoritos, a lista aparece vazia.

#### FR-10: Receber e-mail

A conta recebe e-mail do que o radar encontrou, sem precisar abrir o sistema todo dia. Ela escolhe o que entra no aviso e com que frequência.

**Consequências:**

- A conta liga ou desliga aviso de imóveis novos e aviso de redução de preço.
- A frequência é imediata, uma vez por dia ou uma vez por semana. O padrão mostrado é uma vez por dia.
- O link abre o anúncio.
- O mesmo anúncio e o mesmo fato (novo, ou a mesma mudança de preço) entram no máximo uma vez no período da frequência escolhida.

## 5. O que isto não é

- Não é CRM, gestão de lead, pipeline comercial nem o sistema interno da imobiliária.
- Não é aplicativo.
- Não é chat de inteligência artificial, RAG nem fine tuning nesta versão.
- Não é monitoramento do Brasil inteiro. Nesta versão, é o ABCD.
- Não é um acesso diferente para corretor e imobiliária. A visão é a mesma.
- Não usa cor escura como base da interface.

## 6. Escopo desta versão

### 6.1 Dentro

- Portal público com produtos e planos, no mesmo site da área do cliente.
- Conta de corretor com CRECI ou imobiliária pessoa jurídica, mesma visão.
- 14 dias grátis, no máximo 10 pesquisas, depois bloqueio até ativar um plano. Plano pago com cota mensal e recarga de créditos sem mudar de plano.
- Radar no ABCD, inclusive filtro por imobiliária anunciante.
- Coleta, normalização, anúncio novo, mudança de preço, histórico de preço.
- Dashboard, favoritos e e-mail diário.
- 2 ou 3 fontes para começar: ZAP Imóveis, Viva Real e OLX.

### 6.2 Fora

- WhatsApp. Depois do e-mail.
- Score de oportunidade e IA. Depois que o monitoramento estiver em uso.
- RAG e fine tuning. Ambição de origem, fora desta versão.
- Várias permissões dentro da mesma conta, login social e SSO.
- Mais de uma região além do ABCD, dezenas de fontes, CRM e aplicativo.

## 7. Como saber se deu certo

**Primário**

- **SM-1:** 5 a 10 contas usam o radar de verdade, e algumas voltam toda semana para achar oportunidade. Valida FR-5, FR-7 e FR-8.
- **SM-2:** anúncio novo e mudança de preço aparecem corretos no radar correspondente. Valida FR-6 e FR-7.

**Secundário**

- **SM-3:** o radar é criado em menos de 2 minutos. Valida FR-5.
- **SM-5:** cerca de 90% das contas encontram uma oportunidade relevante sem treinamento, no caminho abrir, filtrar, encontrar e abrir o anúncio. Valida FR-8.
- **SM-4:** 95% das coletas sem erro crítico, com 1.000 anúncios ou mais monitorados. O começo é ZAP Imóveis, Viva Real e OLX. Valida FR-6.

**Não otimizar isto**

- **SM-C1:** quantidade de cadastros. Se a conta não volta, o problema é o valor percebido, não o volume de contas. Contrapeso de SM-1.

## 8. Monetização

| Plano | Pesquisas incluídas | Valor |
| --- | --- | --- |
| Grátis | 10 em 14 dias. Sem compra de crédito. | R$ 0 |
| Padrão | 30 por mês. | R$ 97 por mês |
| Plus | 100 por mês. | R$ 197 por mês |
| Personalizado | Quantidade combinada no contato. | Sob consulta |
| Créditos | Pacote de 10, somado à conta, sem mudar o plano. | R$ 47 |

As funções de monitoramento são as mesmas em todos os planos pagos. A diferença é a cota. A cota do mês não acumula. O crédito comprado não vence nesta versão e só é gasto depois da cota. Cada pesquisa inclusa no padrão sai a cerca de R$ 3,23. No plus, a cerca de R$ 1,97. No pacote avulso, a R$ 4,70. Recarregar custa mais por pesquisa do que subir para o plus.

## 9. Forma

Web, um portal só. Página pública e área do cliente no mesmo site. A stack e o isolamento entre contas estão no `addendum.md`.

### Aparência

Fundo claro. Cor escura não é a base do portal nem da área do cliente.

A paleta segue o que é habitual em SaaS e em sistemas de imobiliária, para a pessoa reconhecer o tipo de produto, com um toque mais moderno. A interface não fica rígida. A escolha dos tons fica para o desenho de UX. A direção foi confirmada em 2026-09-23.

## 10. Perguntas em aberto

Definidas em 2026-09-29. Preços e fontes fechados na mesma data. Não há pergunta de produto em aberto para o planejamento dos épicos.

## 11. Premissas

- `[ASSUMPTION: UJ-2 entrou a partir da narração do bloqueio, sem uma correção posterior dessa cena.]`
- `[ASSUMPTION: o comportamento da área do cliente que não foi narrado de outro jeito segue MVP/mvp.md. A stack desse esboço não segue. Ela está no adendo.]`
- `[ASSUMPTION: o crédito comprado não vence, e a cota do plano não acumula. CRECI e CNPJ são conferidos pelo formato, sem consulta externa.]`
- RAG e fine tuning não fazem parte desta versão. Registrado no adendo.
- A promessa de monitorar e avisar, a sessão segura, o bairro no radar, a configuração do e-mail e a meta de 90% no dashboard voltaram do MVP na reconciliação de 2026-09-23.
- A interface é clara, alinhada ao visual habitual de SaaS imobiliário, mais moderna e menos rígida. Tons específicos ficam para o UX.
