# Epic 1 Context: Entrar e ter cota

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

O visitante vê, no mesmo site, o que o rondimob faz e quanto custa, cria conta de corretor ou de imobiliária e entra numa área única. A conta experimenta o grátis, depois ativa um plano pago ou soma créditos, e só lê o que é dela. Este épico entrega o portal, a sessão e a cota; radar, coleta e aviso ficam para os épicos seguintes.

## Stories

- Story 1.1: Ver produtos e planos no portal
- Story 1.2: Criar conta de corretor ou de imobiliária
- Story 1.3: Entrar, sair e recuperar a senha
- Story 1.4: Uma conta não lê a outra
- Story 1.5: Usar o grátis e ver o bloqueio
- Story 1.6: Ativar plano pago
- Story 1.7: Recarregar créditos

## Requirements & Constraints

Quem cria conta é corretor com CRECI ou imobiliária pessoa jurídica. Comprador, investidor pessoa física e quem espera CRM, aplicativo ou chat ficam de fora. Os dois tipos autorizados veem a mesma área; o que muda é o cadastro. CRECI é número mais UF, conferido só no formato, sem consulta ao conselho. CNPJ tem 14 dígitos e dígitos verificadores válidos, sem consulta à Receita. A imobiliária informa razão social, CNPJ, responsável, e-mail e telefone. E-mail já usado não cria outra conta. Sem login social, SSO nem vários papéis na mesma conta.

O portal público, sem login, mostra os produtos, os quatro planos e o pacote de crédito, e a entrada da área do cliente. Preços: Grátis R$ 0, com 10 pesquisas em 14 dias; Padrão R$ 97 por mês, com 30 pesquisas; Plus R$ 197 por mês, com 100 pesquisas; Personalizado sob consulta, sem gravar cota nem ativar plano; pacote R$ 47 por 10 pesquisas. As funções de monitoramento são as mesmas em todo plano pago; a diferença é a cota.

Pesquisa é uma execução de um radar da conta contra o corpus já gravado. Não gastam pesquisa: criar ou editar radar, abrir resultado já gravado, coleta das fontes, criar conta, entrar na área e abrir a página de planos. Só `contas` altera cota e saldo.

O grátis vale 14 dias-calendário a partir da criação, em America/Sao_Paulo, no máximo 10 pesquisas, sem compra de crédito. No 15º dia sem plano pago, ou com as 10 pesquisas usadas, a conta ainda entra, vê o nome dos radares que já existirem e os planos, e não executa pesquisa, não favorita e não configura alerta. A cota do plano pago é do mês-calendário no mesmo fuso e não acumula: na virada volta a 30 ou 100. Com plano pago, cota do mês em zero e sem crédito, a conta vê resultados já gravados e não executa pesquisa nova.

Crédito soma-se à conta, não ao plano, não muda o plano e não vence nesta versão. Gasta-se só depois que a cota do mês chega a zero. Conta grátis não recarrega; o produto pede ativação de plano. Ativar plano e somar crédito são mudança de estado, sem gateway de pagamento.

A sessão vale até o logout e só para aquela conta. O pedido de nova senha sai do request e vira tarefa do worker; o fornecedor de e-mail ainda não está escolhido. O link define senha nova e a antiga deixa de entrar.

Anúncio de mercado não tem dono de conta. Radar, favorito, alerta, crédito, visto do radar, envio e dados da conta são privados.

## Technical Decisions

Projeto greenfield, sem template. Um app web atende portal público e área do cliente; o worker é outro processo, no mesmo código. Um PostgreSQL, um Redis. Stack: Python 3.13.15, Django 6.1.1, PostgreSQL 18.6, Celery 5.6.3, Redis 8.10.2.

Pastas deste épico: `config` (settings, entrada web e entrada worker) e `contas` (cadastro, sessão, planos, saldo). Um schema só; django-tenants não entra.

Dados privados usam `ENABLE` e `FORCE ROW LEVEL SECURITY`. Os papéis da web e do worker não são superuser, não são donos dessas tabelas e não têm `BYPASSRLS`. Dentro da transação, antes das queries privadas, o código chama `set_config('app.conta_id', ..., true)`. Toda policy lê `app.conta_id`. O valor morre com a transação. Identificador exposto de conta e de crédito é UUID. Saldo de crédito é inteiro.

Recuperação de senha e envio de e-mail não rodam dentro do request HTTP. A migração entra antes de a web e o worker novos atenderem. Log é a saída padrão dos dois processos. Backup é dump do único Postgres. O hospedeiro continua em aberto. Nenhum módulo integra Mercado Pago, Stripe ou outro gateway até uma decisão posterior nomear um.

## UX & Interaction Patterns

Não há documento de UX. A direção visual já fechada: fundo claro; cor escura não é a base do portal nem da área do cliente; visual habitual de SaaS imobiliário, mais moderno e menos rígido. A paleta concreta e a biblioteca de interface ficam em aberto.

Página pública e área autenticada no mesmo site. A entrada da área do cliente é óbvia e pede e-mail e senha. A área é enxuta. Corretor e imobiliária caem na mesma visão.

## Cross-Story Dependencies

O portal e o app nascem antes do cadastro. O isolamento da conta é o padrão que radar, favorito, alerta, crédito, visto do radar e envio repetem quando essas tabelas nascerem. Nesta leva, só os dados da conta recebem a policy; o crédito recebe a mesma policy quando a tabela de saldo for criada.

O portão de grátis e de bloqueio fica em `contas` para as histórias futuras consultarem antes de pesquisa, favorito e alerta. Essas telas ainda não existem aqui. A cota mensal só passa a valer quando o plano pago é ativado. A recarga depende de plano pago já gravado e gasta a cota do mês antes do saldo.

A recuperação de senha depende do worker existir, mesmo sem fornecedor de e-mail. Épicos seguintes criam radar e coleta; este épico não executa pesquisa de verdade, só o contador e o portão que vão aceitar ou recusar essa execução.
