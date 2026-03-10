# Simulation

## Purpose
This document defines the baseline simulation and backtesting assumptions for `options_algo_v2`.

For options systems, simulation assumptions are critical. A weak simulation framework can create false confidence even when the strategy logic appears sound.

This document exists to prevent unrealistic backtests.

---

## 1. Simulation Philosophy

The simulation engine must:

- reflect the actual rulebook
- avoid lookahead bias
- use realistic options chain availability
- include execution frictions
- distinguish theoretical edge from executable edge

The objective is not to maximize backtest returns. The objective is to estimate whether the rulebook can plausibly survive real-world execution constraints.

---

## 2. What the Simulation Must Respect

The simulator must respect:

- universe version
- regime classification rules
- directional classification rules
- IV-state classification rules
- event exclusion rules
- liquidity filters
- expiry and strike tie-break rules
- spread-width ceilings
- sizing rules
- no-roll policy
- exit rules
- monitoring cadence

Backtests must not quietly “cheat” by using looser assumptions than live/paper rules.

---

## 3. Time and Data Conventions

### Time conventions
- DTE = calendar days
- IV/HV windows = trading days
- signal generation timestamps must be explicit
- execution timestamps must be explicit

### Data requirements
Backtests require:
- historical underlying bars
- historical options chain snapshots
- historical contract metadata
- event calendar history
- quote timestamps and freshness context where available

---

## 4. Chain Selection and Historical Availability

The simulator must only use contracts that would have been available and liquid at the decision time.

### Must not do
- select strikes or expiries using future chain state
- assume ideal contract existence if no historical record exists
- use chain data from after the supposed execution timestamp

### Must do
- reconstruct the eligible chain at decision time
- apply the same deterministic expiry and strike rules as live logic
- reject trades when a compliant structure cannot actually be built

---

## 5. Fill Assumptions

This is the most important realism section.

## 5.1 Never assume guaranteed midpoint fills
The simulator must not assume that all spreads are filled at midpoint.

## 5.2 MVP fill model
### Credit spreads
Entry fill assumption:
- midpoint minus slippage buffer

### Debit spreads
Entry fill assumption:
- midpoint plus slippage buffer

### Exit fill assumption
For exits:
- adverse to midpoint by same or slightly worse slippage assumption

## 5.3 Slippage model
Slippage should depend on:
- spread width as percentage of mid
- contract liquidity
- time of day
- chain quality

### Minimum starter approach
Apply a configurable adverse fill penalty:
- fixed percentage of mid
- with additional penalty for poorer spread quality buckets

---

## 6. Execution Non-Fill Logic

The simulator should allow for non-fills.

A candidate trade should be rejected or marked unfilled if:
- spread quality exceeds allowed threshold
- no compliant combo price could reasonably execute within slippage budget
- one leg lacks sufficient liquidity

This matters because many false-positive options backtests come from assuming all modeled signals become filled trades.

---

## 7. Liquidity Realism

The simulator must incorporate:

- minimum OI thresholds
- minimum previous-day volume thresholds
- bid/ask spread thresholds
- stale/invalid quote rejection where possible

A trade should not exist in the simulation if it violates live liquidity rules.

---

## 8. Event Realism

The simulator must enforce the same event rules as the live rulebook:

- no earnings event inside planned holding window
- optional event caution buffers if configured
- ex-div caution logic logged or enforced if activated

No trade should remain in the backtest if it would have been excluded in production.

---

## 9. Exit Realism

The simulator must apply:

- profit target exits
- loss exits
- time exits
- event exits
- exit priority ordering

Exit logic must be evaluated using the same cadence assumptions as the live monitoring model for that phase.

---

## 10. Monitoring Cadence in Simulation

MVP simulation should mirror MVP operational cadence:
- nightly evaluation
- pre-market qualification
- scheduled intraday monitoring windows

Not tick-by-tick reactive monitoring.

This keeps simulation aligned with intended system operations.

---

## 11. Assignment / Exercise / Expiration Considerations

For MVP:
- use defined-risk verticals only
- close before final high-risk expiry windows per rulebook
- do not intentionally simulate holding to expiration as a normal exit path

### Note
Early assignment and ex-dividend edge cases should at minimum be:
- logged in simulation outputs
- flagged for later model improvement

---

## 12. Cost Model

The simulator must support:
- commissions
- fees
- slippage
- optional borrow/assignment-related frictions later if relevant

At minimum, the simulation must report:
- gross results
- net-of-cost results

If a strategy only works gross and not net, it does not work.

---

## 13. Portfolio Simulation Requirements

The portfolio simulator should support:
- max open positions
- max risk per trade
- max per sector
- max per underlying
- max same-direction concentration
- expiry clustering limits if enabled

It must not allow the backtest to “take everything” if live rules would not.

---

## 14. Stress Testing

The simulation framework should support scenario stress testing.

### Per-position stress examples
- underlying move: -2%, -4%, -6%, +2%, +4%
- IV shock: +5 vol points, +10 vol points
- time passage: 1 day, 3 days

### Portfolio stress examples
- correlation spike
- broad gap move
- volatility expansion across all positions

Stress testing helps detect concentration risk hidden by ordinary backtest summaries.

---

## 15. Metrics to Report

### Trading metrics
- expectancy per trade
- average return on max risk
- max drawdown
- profit factor
- win rate
- average hold time
- PnL by regime
- PnL by IV state
- PnL by strategy family

### Execution realism metrics
- average entry slippage
- average exit slippage
- % no-fill
- % rejected for liquidity
- % rejected for event risk

### Operational metrics
- number of candidate signals
- number of qualified signals
- number of filled trades
- number of closed trades
- rejection reasons distribution

---

## 16. Simulation Guardrails

The simulator must avoid:

- lookahead bias
- universe drift without versioning
- chain survivorship bias where possible
- guaranteed midpoint fills
- ignoring missing/invalid data
- using future-known Greeks or contract conditions
- using a more permissive ruleset than production logic

---

## 17. Baseline Comparison Policy

Every strategy backtest should be compared against at least:

- no-trade filtered baseline
- single-structure-only baseline
- structure-adaptive baseline

This helps test whether structure selection is adding value.

---

## 18. Simulation Deliverables

Before live or semi-live progression, the system should be able to produce:

- deterministic backtest reports
- trade logs with reasons
- rejection reason breakdown
- fill assumption sensitivity analysis
- parameter version references
- universe version references
- strategy/risk config version references

---

## 19. Conclusion

The simulator is not just a reporting tool. It is the realism filter for the strategy.

If the strategy only survives under:
- perfect fills
- loose chain assumptions
- no event realism
- no liquidity constraints

then the strategy should be considered unproven.

Simulation discipline is part of the edge-validation process.
