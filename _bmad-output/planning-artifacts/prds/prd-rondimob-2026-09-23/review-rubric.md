# PRD Quality Review — rondimob (prd-rondimob-2026-09-23)

## Overall verdict
The PRD holds a clear monitoring thesis — ABCD price-and-competitor watch for CRECI brokers and PJ agencies — with honest non-goals, coherent feature arc, and success metrics that test the bet rather than vanity. What is at risk is done-ness on the account and monetization edges: free-tier “pesquisa,” CRECI/PJ verification, plan differentiation, and the post-trial blocked state remain open while FR-9 and soft alert language leave story writers without testable consequences. As a draft for UX / architecture / stories it is usable; as a build-freeze gate it is not.

## Decision-readiness — adequate
Trade-offs are named as decisions, not smoothed away: monitoring is in practice; “RAG e fine tuning ficam para depois” (§1); CRM, app, AI chat, Brazil-wide coverage, and dark UI are explicit outs (§5, §6.2). Monetization (§8) and UJ-2 (§2.3) state plainly that paid-plan price and differentiation “ainda não têm valor” / “não foi definida,” and Open Questions (§10) are real opens rather than rhetorical. The draft framing (“Não bloqueiam este rascunho”) matches status. What weakens actability is the soft escape in Vision — “Se o resultado não for o esperado, o produto se ajusta” (§1) — and the absence of `[NOTE FOR PM]` at the real tension the Premissas already admit: UJ-2 was written from narration “sem correção posterior” (front matter; §11). A decision-maker can green-light monitoring scope; they cannot yet green-light the paid conversion path.

### Findings
- **high** Paid conversion path undecidable (§2.3 UJ-2; §8; §10 itens 4–5) — Plans appear on the public portal (FR-1) and unlock use (FR-4), but “A diferença entre o que cada plano libera não foi definida” and blocked-state visibility “não foi narrado.” *Fix:* Either mark FR-1/FR-4/UJ-2 as blocked until Rafael closes OQ4–5, or ship a temporary single paid SKU with explicit “all monitoring unlocked” so the gate is testable.
- **low** Vision softens commitment (§1) — “Se o resultado não for o esperado, o produto se ajusta” reads as a non-decision. *Fix:* Replace with a stated review criterion tied to SM-1/SM-2 (e.g. adjust scope if SM-1 fails after N weeks).

## Substance over theater — strong
Vision is category-specific and would not survive a find-replace into another real-estate SaaS: “o lugar único em que o corretor e a imobiliária acompanham preço por região e concorrentes no ABCD” (§1). Personas are load-bearing — Vinicius drives UJ-1/UJ-2 and FR examples — not a four-persona gallery. Innovation ambition (RAG / fine tuning) is parked in the addendum instead of padded into FRs. Where NFRs appear they carry product thresholds (radar “em menos de 2 minutos” in §4.3; “95% das execuções sem erro crítico” in FR-6), not generic “must be scalable.” The appearance section is intentionally directional for UX rather than fake-precision palette theater.

### Findings
*(none — furniture is scarce; deferrals are earned.)*

## Strategic coherence — strong
The thesis is monitoring-as-the-product for a geographic niche; every in-scope FR (portal → gated account → radar → collect/normalize → new/price-change → dashboard/favorites/email) serves that arc. Prioritization follows the thesis, not ease: score/IA/WhatsApp/CRM are out until “o monitoramento estiver em uso” (§6.2). Success metrics validate the bet — SM-1 requires real radar use and weekly return “para achar oportunidade”; SM-C1 explicitly counters optimizing “quantidade de cadastros” (§7). MVP kind is problem-solving (stop opening each portal), and scope logic matches.

### Findings
*(none material.)*

## Done-ness clarity — thin
Core monitoring FRs earn their keep: FR-6 and FR-7 give concrete consequences (per-source failure isolation, price normalization examples, dedupe rule, identity preference “fonte mais identificador externo”). Account and engagement FRs do not. FR-9 is a capability list with no **Consequências** block. FR-10’s “O mesmo fato não se repete de forma excessiva no mesmo dia” is an adjective, not a bound. FR-2’s “não conclui o cadastro” and FR-4’s “11ª pesquisa” are untestable until OQ2 and OQ1 close — the Glossary itself marks both as “em aberto.” FR-8 counts “oportunidades” on the home screen while §6.2 defers “Score de oportunidade,” with no definition of what the count means.

### Findings
- **high** FR-9 has no testable consequences (§4.5 FR-9) — Only “favorita, desfavorita, vê a lista… e abre o anúncio.” *Fix:* Add consequences (persistence across sessions, isolation per FR-3, open-original URL, empty state).
- **high** Free-tier unit “pesquisa” is undefined (§3 Glossário “Pesquisa”; §4.2 FR-4; §10 item 1) — “A 11ª pesquisa no período grátis não é aceita” cannot be verified. *Fix:* Define the unit (radar create? dashboard query? email digests?) before stories for FR-4.
- **high** “Oportunidades” on the dashboard is undefined while opportunity score is out of scope (§4.5 FR-8; §6.2) — “quantidade de novos, de quedas de preço e de oportunidades” invites builders to invent a score. *Fix:* Define oportunidade as a named rule (e.g. new ∪ price-drop ∩ radar) or drop the third counter until score ships.
- **medium** FR-10 anti-spam language is unbounded (§4.5 FR-10) — “não se repete de forma excessiva.” *Fix:* Bound it (at most once per anúncio per fato per dia).
- **medium** CRECI / PJ verification leaves FR-2 acceptance open (§4.2 FR-2; §10 item 2) — “Quem não se enquadra não conclui o cadastro” without how. *Fix:* State MVP rule (honor-system + format check vs. manual review vs. API) even if temporary.

## Scope honesty — strong
Omissions do real work. §5 and §6.2 name CRM, app, AI chat, RAG/fine tuning, Brazil-wide monitoring, divergent corretor/imobiliária UX, dark base UI, WhatsApp, multi-permission, and plan economics. In-FR outs appear where useful (“Fora deste requisito: login social, SSO…” in FR-2). Premissas (§11) admit UJ-2 was uncorrected and that client-area behavior “segue `MVP/mvp.md`.” Open-item density (six questions + several “em aberto”) fits a draft; the PRD does not pretend those are closed. Formal `[ASSUMPTION]` / `[NOTE FOR PM]` / `[NON-GOAL for MVP]` tags are missing — honesty is present in prose, not in the rubric’s callout grammar.

### Findings
- **medium** Premises and tensions lack formal tags (§11; front matter; §10) — No `[ASSUMPTION: …]`, no Assumptions Index, no `[NOTE FOR PM]` at UJ-2 narration risk or MVP.md dependency. *Fix:* Tag UJ-2-uncorrected, MVP.md-as-behavior-source, and stack-in-addendum as assumptions; index them at the end.
- **low** Open Questions claim non-blocking for the draft (§10) — Fine for status:draft; unsafe if someone treats the file as build-ready. *Fix:* Split “blocks rascunho” vs. “blocks implementação de FR-2/FR-4/UJ-2.”

## Downstream usability — adequate
§0 states the audience (UX, architecture, stories). Glossary covers the main domain nouns; FR-1…FR-10, UJ-1…UJ-2, SM-1…SM-4 / SM-C1 are contiguous and unique; UJs name Vinicius as protagonist. Cross-doc hygiene is partial: UJ-1 step 4 says “O resto da sessão segue o MVP” without lifting those consequences into the PRD, so story extraction must open `MVP/mvp.md` (whose stack the addendum already overrides). FR-3 lists “alerta” as a private object alongside radar/favorito, but the only notification FR is e-mail (FR-10) — glossary has no **Alerta**. Architects must read the addendum for Django/Postgres/Celery; that split is intentional and documented.

### Findings
- **medium** “Alerta” appears without a defined object (§4.2 FR-3) — “radar, favorito, alerta nem configuração.” *Fix:* Glossary entry equating alerta to e-mail digests (FR-10) or remove the noun.
- **medium** Client-area path outsourced to MVP.md (§2.3 UJ-1 passo 4; §11) — “O resto da sessão segue o MVP: dashboard… e-mail diário” / “segue `MVP/mvp.md`.” *Fix:* Ensure every MVP behavior relied on is already a numbered FR consequence (most are; call out any residual gaps explicitly).
- **low** Chain-top split across PRD + addendum (§0; addendum) — Correct separation, but easy to miss RLS / queue-per-fonte decisions. *Fix:* One-line pointer in §6.1 or Forma: “stack e isolamento no addendum.”

## Shape fit — strong
Multi-stakeholder B2B with meaningful UX and chain-top intent (§0) — UJs with named protagonists and a glossary are the right load-bearing shape, not overhead. Formality is lean (two journeys, one shared client area), matching a solo/hobby-adjacent stakes product that still feeds UX and architecture. Not under-formalized (consumer-grade monitoring SaaS without journeys) and not over-formalized (no persona gallery, no regulatory matrix). Brownfield conflict (MVP.md FastAPI/Angular vs. addendum Django) is handled in the addendum rather than silently ignored.

### Findings
*(none — shape matches the product.)*

## Mechanical notes
- **Glossary drift:** “alerta” used in FR-3 without glossary entry; “oportunidades” / “oportunidade” used in FR-8, SM-1, and non-goals (score) without a single definition; “Pesquisa” and “Plano” correctly flag “em aberto.”
- **ID continuity:** FR-1–FR-10, UJ-1–UJ-2, SM-1–SM-4, SM-C1 — contiguous, unique; FR↔UJ↔SM cross-refs in §4/§7 resolve.
- **Assumptions Index roundtrip:** no inline `[ASSUMPTION]` tags and no index — Premissas (§11) are prose-only.
- **UJ protagonists:** UJ-1 and UJ-2 both carry Vinicius (imobiliária as same scene) — OK.
- **Required sections for stakes:** Vision, users/UJs, glossary, FRs, non-goals, scope in/out, SMs + counter-metric, monetization honesty, open questions, premissas, addendum for stack — present for a draft chain-top PRD.
- **External consistency:** addendum correctly notes MVP.md still cites FastAPI/Angular and that behavior (not transport) remains the PRD input.
