# Execution

## Purpose
This document defines the MVP execution policy for `options_algo_v2`.

The MVP is not designed for unattended live deployment. However, execution rules must still be explicit so that:

- paper trading is realistic
- semi-manual workflows are consistent
- later broker integration does not invent policy on the fly

---

## 1. Execution Philosophy

Execution should preserve edge, not destroy it.

This means:
- no forcing trades in poor chain conditions
- no market orders for spreads
- no manual legging by default
- bounded repricing only
- no rescue rolling
- explicit no-fill state

Good execution policy is part of risk control.

---

## 2. Allowed Entry Style

For MVP, all entries are:

- limit combo orders only

Not allowed by default:
- market orders
- legging into spreads manually
- discretionary repricing outside policy
- rolling into replacement structures

---

## 3. Pre-Execution Qualification

Before any order is drafted, the trade must still pass:

- regime permission rules
- event-window exclusion rules
- liquidity qualification rules
- quote freshness rules
- portfolio-cap rules
- system health checks

If any fail:
- no order is created

---

## 4. Quote Quality Requirements

During live market hours:

- underlying quote age <= 10 seconds
- option quote age <= 60 seconds
- no crossed markets
- both legs must have valid bid and ask
- spread quality must remain within policy

If quote quality degrades:
- reject the entry
- or cancel pending order if no fill yet

---

## 5. Order Drafting

A qualified signal becomes an order draft only after:

1. expiry is selected
2. strikes are selected
3. width complies with policy
4. risk sizing is computed
5. expected max loss is within portfolio limits
6. execution-quality checks pass

Order draft should include:
- signal_id
- strategy_type
- underlying
- expiry
- strikes
- side
- width
- target credit/debit
- max loss
- slippage budget
- order timestamp

---

## 6. Entry Pricing Policy

### 6.1 Credit spreads
Initial limit price:
- modeled fair credit = midpoint - slippage buffer

### 6.2 Debit spreads
Initial limit price:
- modeled fair debit = midpoint + slippage buffer

### 6.3 Fair-price intent
The goal is not to demand perfect midpoint fills.
The goal is to enter only if execution remains inside the allowable slippage budget.

---

## 7. Repricing Policy

### MVP repricing rules
- maximum repricing attempts: 3
- maximum repricing window: 5 minutes
- each reprice must remain within max slippage budget

If still not filled:
- mark order as CANCELED
- mark signal outcome as NO FILL / EXPIRED SIGNAL

---

## 8. Slippage Budget

Default MVP budget:
- adverse execution may not exceed 10% relative to modeled midpoint economics

If execution requires worse terms:
- reject entry

This prevents low-quality fills from turning valid research into poor realized trades.

---

## 9. No-Fill Rules

A signal becomes NO FILL if:
- repricing policy exhausted
- spread widens beyond policy
- one leg loses liquidity
- quote becomes stale
- underlying moves beyond entry tolerance
- system health degrades during submission window

This is a valid and expected operational outcome.

---

## 10. Exit Execution Policy

Exit orders should also follow disciplined limit-based logic where possible.

### Exit types
- event exit
- loss / invalidation exit
- time exit
- profit target exit
- emergency exit

### Exit priority order
1. system / ops emergency exit
2. event exit
3. hard loss / technical invalidation
4. time exit
5. profit target

### Exit behavior
If position must be closed:
- submit defined-risk spread exit as combo where possible
- do not leg out by default unless policy later supports it
- respect urgency of exit type

---

## 11. Emergency Exit Policy

Emergency conditions include:
- system-degraded state
- severe broker issue
- contract reconciliation mismatch
- unexpected quote/data failure with open risk
- operator override

In an emergency:
- preserving capital and reducing unmanaged exposure takes priority over pricing efficiency

Emergency actions should be logged with clear reason codes.

---

## 12. Lifecycle State Model

### Signal states
- CANDIDATE
- QUALIFIED
- REJECTED
- EXPIRED

### Order states
- ORDER_DRAFTED
- ORDER_SUBMITTED
- PARTIALLY_FILLED
- FILLED
- CANCELED
- REJECTED

### Position states
- OPEN
- EXIT_PENDING
- CLOSED

All execution and lifecycle transitions must be auditable.

---

## 13. No-Roll Rule

MVP rule:
- no rolling
- no adjustment structures
- close only

This is intentionally restrictive.

Reasons:
- easier attribution
- cleaner simulation
- easier monitoring
- less discretionary drift

---

## 14. Broker Role in MVP

For MVP:
- broker integration is secondary to deterministic rule enforcement
- execution can be paper, semi-manual, or simulated
- live broker routing should not become the critical path before rule stability is proven

IBKR is expected to support:
- order routing
- fill state
- position reconciliation
- held-position quote checks

It is not the strategy-definition source of truth.

---

## 15. Operator Override Policy

MVP should allow operator overrides only in explicit categories:

- emergency cancel
- emergency close
- reject due to obvious market abnormality not yet encoded
- manual broker-level reconciliation

Overrides must be:
- logged
- reason-coded
- distinguishable from systematic decisions

This keeps the dataset clean.

---

## 16. Execution KPIs

The system should track:
- fill rate
- no-fill rate
- average entry slippage
- average exit slippage
- average time-to-fill
- cancellation rate
- order rejection rate
- mismatch rate between modeled and realized execution

These metrics are crucial before any move toward automation.

---

## 17. Conclusion

The MVP execution policy is intentionally conservative.

Its purpose is to:
- protect edge
- preserve auditability
- support realistic paper trading
- avoid discretionary drift
- build a trustworthy base for later automation

A clean execution policy is part of the strategy, not an afterthought.
