# Data Contract Impact Checker

[![CI](https://github.com/MadanMohan0537/data-contract-impact-checker/actions/workflows/ci.yml/badge.svg)](https://github.com/MadanMohan0537/data-contract-impact-checker/actions/workflows/ci.yml)

**Treat data quality as an agreement between the team that produces a dataset and the teams that consume it: check each batch against a versioned contract, return a pass, warn, or block decision, and preview which declared consumers a schema change affects.**

A dependency-free Python MVP. The Python package name stays `schemapact`, and the CLI is `python -m schemapact.cli` (console script: `schemapact`).

## Problem and who it's for

Data-quality tests usually live with one team and answer one question: did this batch pass? They leave two later questions open: who downstream will break, and whether a planned schema change (a rename, a removed field, a tighter range) is safe to make. The people who need those answers are data producers, analytics engineers, and the PMs and owners of dashboards or models that depend on a table.

## Approach

- A **contract** declares the producer, a freshness SLA in hours, and each field's type, required flag, nullability, whether that field is critical, an optional minimum, an optional maximum, and an optional set of allowed values. Consumers declare which fields they use.
- The **checker** returns `PASS`, `WARN`, or `BLOCK`. The decision is `BLOCK` when any breach is critical, `WARN` when every breach is a warning, and `PASS` when there are no breaches. A critical field produces critical breaches; other fields produce warnings. `STALE` is always critical. Each breach keeps its code, the affected row indexes, and a detail string. Breach codes are `STALE`, `MISSING_FIELD`, `NULL`, `TYPE`, `MIN`, `MAX`, and `ALLOWED`.
- A **notice** is a fixed template. A passing batch says the dataset passed. A failing batch names the dataset, contract version, decision, breach count, the producer, and the declared consumers whose fields appear in the breaches.
- A **migration preview** compares two contract versions. A rename, a removal, a type change, or a tighter minimum, maximum, or nullability rule is recorded as a breaking change with a staged migration proposal. The preview walks fields on the old contract. An added field, including the optional-field control in the tests, produces no impact, so the preview stays safe.
- **Lineage coverage** is declared consumers divided by a caller-supplied known-consumer count, capped at `1.0`. A known count of `0` yields `1.0`. When the count is omitted, it defaults to the declared count, so coverage is `1.0`.

```text
contract + batch -> checker -> PASS / WARN / BLOCK -> notice
       |
       + old/new versions + field usage -> migration preview + coverage
```

## What exists today

Checked in this repository on Python 3.12.3: `python -m unittest discover -s tests -v` ran 20 tests, all passing, and `python -m schemapact.cli --output report.json` printed the demo result below.

The CLI demo copies the orders fixture, sets the second row's `amount` to `-4`, and checks the batch at age 30 hours against the fixture's 24-hour SLA. Printed result:

- decision `BLOCK`
- 2 breaches: critical `STALE`, and critical `MIN` on `amount` at row index 1
- affected consumers `revenue-dashboard` and `risk-model`
- lineage coverage `0.75`

The consumer names in that summary come from the migration preview. The check notice names the same two consumers because they use `amount`. The preview renames `amount` to `total_amount` and proposes dual-publishing both names, then migrating consumers, then removing the old name. The replacement field is also created with minimum `10`; that tighter minimum is not a second impact, because the field is handled as a rename. The fixture declares three consumers. `fulfillment` does not use `amount`, so it is absent from this list. Coverage is `0.75` because the demo passes `known_consumer_count=4` (3 declared). The undeclared count is 1. The demo does not name a fourth consumer.

The 20 tests also cover a clean batch (`PASS`), a stale batch (`BLOCK`), a negative critical amount (`BLOCK`), a disallowed non-critical `status` (`WARN`), a missing critical field (`BLOCK`), a `TYPE` breach, a `NULL` breach, the row index stored for a `MIN` breach, and rejection of a duplicate field, an unknown type, and a minimum greater than the maximum. Migration tests rename `amount` to `total` and expect consumers `revenue-dashboard` and `risk-model`, and they assert that rename is unsafe. They assert removal of `status` (`removed`), a type change (`type_changed`), and a tighter minimum (`tightened`). In the checker those three impacts are created with breaking severity. Adding an optional nullable field leaves the preview safe. Coverage is `0.75` when the known count is 4, and the undeclared count is 2 when the known count is 5. No test asserts a `MAX` breach; the maximum check exists in the checker.

`examples/orders-v1.toml` is a partial illustration (dataset, version, producer, freshness, `order_id`, and `amount`). It omits `customer_id`, `status`, and every consumer. The checker does not load it. The contract the tests and CLI use is the Python fixture in `schemapact/fixtures.py`. The CLI writes `report.json`.

`.github/workflows/ci.yml` installs the package and runs the same unit tests and CLI on Python 3.11, 3.12, and 3.13. The commands in this section were run here on Python 3.12.3 only.

## How success would be measured

| Measure | Status |
|---|---|
| Breaking changes caught before a real release | Not yet measured |
| Downstream incidents traced to undeclared consumers | Not yet measured |
| Declared lineage coverage on a real catalog | Not yet measured |
| Time from a failed batch to the right owner being notified | Not yet measured |

The `BLOCK` decision, the two-consumer rename preview, and coverage `0.75` are fixture results from the tests and CLI demo. No committed measurement from a live catalog, a release, or an incident log is in this repository.

## Limitations

- Contracts are Python objects. `examples/orders-v1.toml` is an example file. There is no TOML loader and no contract registry.
- Freshness compares a caller-supplied age in hours with `freshness_hours`. The checker does not read pipeline timestamps.
- Notices are deterministic templates. Nothing is sent.
- Consumers are declared on the contract. They are not read from SQL or a lineage tool. Coverage shows an undeclared gap only when the caller passes a known-consumer count larger than the declared count.
- The preview does not scan fields that exist only on the new contract, and it does not treat a narrower allowed-value set as a change.
- The circuit breaker returns a decision. It does not call an orchestrator such as Airflow or dbt.

See [docs/METHOD.md](docs/METHOD.md) and [docs/BACKLOG.md](docs/BACKLOG.md).

## Quick start

Requires Python 3.11+. No credentials, and no runtime dependencies beyond the Python standard library.

```bash
git clone https://github.com/MadanMohan0537/data-contract-impact-checker.git
cd data-contract-impact-checker
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
python -m schemapact.cli --output report.json
```

## Deployment

Cloudflare Workers is the planned deploy target. Workers is not configured in this repository yet, and this project is not deployed.

Once a Worker exists, the deploy command is:

```bash
npx wrangler deploy
```

That command has nothing to deploy until these exist:

- `wrangler.toml`
- a Worker entry point
- Python Workers support for the `schemapact` package, or a JavaScript/TypeScript port of the checker

## License

MIT. See [LICENSE](LICENSE).
