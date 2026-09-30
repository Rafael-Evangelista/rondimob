- source_spec: `/workspace/_bmad-output/implementation-artifacts/spec-1-2-criar-conta-de-corretor-ou-de-imobiliaria.md`
  summary: The signup view's IntegrityError handler for a duplicate email is not covered by a test.
  evidence: clean_email already rejects an email that exists, so the sequential test passes if the except block is removed. Only an insert that races past that check reaches the handler.
