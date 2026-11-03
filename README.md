# SchemaPact

[![CI](https://github.com/MadanMohan0537/data-contract-impact-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/MadanMohan0537/data-contract-impact-checker/actions/workflows/ci.yml)

SchemaPact makes data quality a producer–consumer agreement rather than an isolated test: versioned contracts define schema, nullability, ranges, freshness, ownership, severity and consumer usage; failures become circuit-breaker decisions and impact-focused notices.

> **Project Lab traceability:** Idea 15 — Data Quality Contracts. SchemaPact is the product name; the original title remains only as metadata.

## Shipped MVP

- Versioned contracts with producer, freshness SLA, fields and consumers
- Type, required, null, range, allowed-value and freshness checks
- Critical failures block downstream work; non-critical failures warn
- Breaches retain codes, affected row indexes and details
- Plain-language notice naming producer and declared impacted consumers
- Consumer lineage and coverage metric
- **P1 compatibility migration preview** for renames, removals, type changes and tightened constraints
- **P1 SQL lineage corroboration** that audits observed contract-field references against consumer declarations
- Exact lineage coverage, undeclared-reference and unknown-consumer evidence
- Staged migration proposals for each breaking change
- TOML contract example, reproducible bad batch, JSON report
- 28 focused tests and Python 3.11–3.13 CI

No credentials, paid services or external dependencies are required.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m schemapact.cli --output report.json
```

The demo injects both a stale batch and a negative critical amount, blocks downstream processing, generates an impact notice, previews an `amount` → `total_amount` migration, and audits three synthetic SQL queries.

## Compatibility experiment

The frozen contract declares three consumers. Renaming `amount` must identify both consumers that use it; removing `status`, changing a type, and tightening a range must also be classified as breaking. Adding an optional field is the non-breaking control. A fourth known-but-undeclared consumer reduces lineage coverage to 75%, making invisible dependencies explicit rather than implying full coverage.

## SQL lineage experiment

Three deterministic query samples contain nine references to contract fields. Eight agree with the declared consumer contracts; the risk model also reads undeclared `status`. The report therefore records 8/9 (88.9%) corroboration and one undeclared reference. Comments and string literals are ignored, and `SELECT *` is conservatively expanded to every contract field.

## Architecture

```text
contract + batch -> checker -> PASS / WARN / BLOCK -> notice
       |
       + old/new versions + field usage -> migration preview + coverage
       + query samples -> SQL corroboration -> drift evidence
```

## Evidence boundaries

This is a portfolio-scale policy engine, not a production catalog. Contracts are Python objects with a TOML example rather than a full parser/registry; timestamps are caller-supplied as age; notices are deterministic templates; and the breaker returns a decision but does not control an orchestrator. SQL corroboration is intentionally scoped token analysis—not a full SQL parser—so dynamic SQL, derived aliases and transitive dependencies can remain invisible. Coverage is always shown rather than presented as certainty. See [method and limitations](docs/METHOD.md), [feature backlog](docs/BACKLOG.md), and [progress record](docs/PROGRESS.md).

## License

MIT

