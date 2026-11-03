# Method and limitations

## Evaluation

The fixture models an orders feed with critical identifiers and amount, plus a non-critical status. The demo seeds a negative amount and a 30-hour-old batch against a 24-hour SLA. Both must contribute to a BLOCK decision.

For the P1 experiment, the proposed contract renames amount to total_amount. The preview compares the versions with declared consumer field usage. Acceptance criteria are fixed in advance: identify both affected consumers, classify rename/removal/type/tightening changes as breaking, keep an optional addition non-breaking, and report 75% coverage when one of four known consumers lacks declarations.

For SQL lineage corroboration, three synthetic queries provide nine observable contract-field references. The fixed acceptance criterion is to match eight declarations and flag the risk model's undeclared `status` reference, producing exact 8/9 coverage. Tests also require comments and quoted literals not to create false lineage, `SELECT alias.*` to expand conservatively, unknown consumers to remain visible, and empty evidence to fail closed.

## Limitations

- No durable registry, authentication, signatures or approval workflow.
- TOML is demonstrated but loading/serialization is not yet implemented.
- Type checks model Python values, not warehouse-specific coercion.
- Row indices may expose sensitive context in real notifications.
- SQL corroboration recognizes contract field tokens and stars; it is not dialect-aware and does not resolve derived aliases, CTE semantics, stored procedures, dynamic SQL or transitive views.
- Query samples have no collection timestamp or representativeness guarantee yet, so coverage is evidence about the supplied sample—not total production usage.
- Incomplete declarations and incomplete query samples can still create false negatives.
- Freshness is passed by the caller and not verified from source metadata.
- Notices are templates, not generated or localized prose.
- The circuit breaker does not integrate with an orchestrator.

