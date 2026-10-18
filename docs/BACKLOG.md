# Feature backlog

| Priority | Feature | User problem | Behavior | Dependencies | Success test | Risks / tradeoffs | Status |
|---|---|---|---|---|---|---|---|
| P0 | Contract checker and breaker | Bad data reaches consumers | Validate batch and block only critical breaches | Python stdlib | Seeded stale/negative batch blocks; warning-only batch continues | Poor severity choices either block too much or too little | Shipped |
| P1 | Compatibility migration preview | Producers cannot see who a schema change breaks | Diff versions against declared field usage and propose staged migration | Versioned contracts, lineage | Rename identifies 2/2 declared affected consumers; controls classify correctly | Undeclared dependencies remain invisible | Shipped |
| P1 | SQL lineage corroboration | Declarations rot silently | Compare declared fields with parsed query references | Query logs, SQL parser | Seeded undeclared field use reduces coverage and alerts owner | Dynamic SQL is hard to parse | Planned |
| P1 | Contract adoption score | Coverage percentage hides critical gaps | Weight coverage by consumer criticality and freshness | Registry, tiers | Missing executive dashboard dependency dominates low-risk sandbox | Scores can be gamed | Planned |
| P2 | Quarantine and repair provenance | One bad row blocks valid records | Split valid/invalid rows and replay repairs with original IDs | Durable batch ledger | No duplicate consumption and full repair lineage | Partial processing changes totals | Planned |
| P2 | SLA acknowledgement workflow | Notices do not ensure ownership | Track owner receipt, acknowledgement and escalation | Identity, messaging | Critical breach acknowledged within tier SLA | Alert fatigue and blame culture | Explored |
| P2 | Constraint drift proposal | Contracts become stale | Suggest bounded changes from stable observed patterns | History and review workflow | Legitimate shift yields reviewable proposal, not auto-change | Normalizes upstream defects | Explored |
| P3 | Consumer rehearsal sandbox | Static diffs miss semantic failures | Replay sampled consumer queries against shadow schema | Safe query runner | Seeded semantic break fails before rollout | Cost and sensitive-query handling | Explored |
| P3 | Blast-radius prioritization | Many consumers make migrations unmanageable | Rank affected paths by business criticality and transitive lineage | Full graph, service tiers | Highest-impact path ranks first | Incorrect tiers distort priority | Explored |
| P3 | Privacy-safe breach evidence | Row examples may expose customer data | Redact/hash samples by field policy | Classification rules | Sensitive seeded values never enter notice | Redaction can impede debugging | Explored |
