# Rulebook

## Version
Rulebook v1.0

## Purpose
This document defines the deterministic MVP trading rules for `options_algo_v2`.

It is the build spec for Phase 1 research and candidate-generation implementation.

---

## 1. Time Convention Standard

Use the following conventions consistently:

- **DTE** = calendar days
- **holding caps** = calendar days
- **IV rank lookback / HV windows** = trading days
- **earnings buffers** = trading days
- **quote freshness thresholds** = wall-clock seconds

---

## 2. Allowed Strategy Types

The MVP supports only:

- Bull Put Spread
- Bear Call Spread
- Bull Call Spread
- Bear Put Spread

No other structures are allowed.

---

## 3. No-Roll Policy

MVP rule:

> No rolling. No adjustments. Close only.

---

## 4. Market Regime States

The system assigns one of:

- TREND_UP
- TREND_DOWN
- RANGE_UNCLEAR
- RISK_OFF

### 4.1 Regime Permissions

| Regime | Bullish Entries | Bearish Entries | New Entries Allowed |
|---|---:|---:|---:|
| TREND_UP | Yes | No | Yes |
| TREND_DOWN | No | Yes | Yes |
| RANGE_UNCLEAR | No | No | No |
| RISK_OFF | No | No | No |
| SYSTEM_DEGRADED | No | No | No |

---

## 5. System Health Kill Switch

A separate operational override state exists:

- SYSTEM_DEGRADED

### Trigger examples
- primary data unavailable
- stale option chains
- DB write failure
- contract resolution mismatch
- broker instability
- pipeline incomplete
- timestamp drift
- excessive fallback usage

### Effect
If SYSTEM_DEGRADED is active:
- no new entries
- no new executable signals
- monitoring only

---

## 6. Universe Policy

The system uses a fixed, versioned universe file.

Example:
- `config/universe_v1.yaml`

Universe membership should remain frozen for a given backtest or ruleset version.

### Eligibility baseline
A symbol is eligible only if:
- underlying price >= $20
- 20-day average stock volume >= 1,000,000 shares
- options chain quality is acceptable

---

## 7. Breadth Definition

Breadth is defined as:

> percent of eligible universe names with close > 20DMA

### Breadth guidance
- bullish support: > 55%
- bearish support: < 45%
- between 45% and 55% contributes to RANGE_UNCLEAR

---

## 8. Underlying Directional States

Each symbol is classified into one of:

- BULLISH_CONTINUATION
- BULLISH_BREAKOUT
- BEARISH_CONTINUATION
- BEARISH_BREAKDOWN
- NEUTRAL
- NO_TRADE

### 8.1 BULLISH_CONTINUATION
Minimum starter conditions:
- close > 20DMA > 50DMA
- ADX >= 18
- RSI between 50 and 70
- 5-day return > 0

### 8.2 BULLISH_BREAKOUT
Minimum starter conditions:
- close > 20DMA and close > 50DMA
- close above rolling 20-day high
- breakout day volume >= 1.5x 20-day average volume
- ADX >= 16 or rising

### 8.3 BEARISH_CONTINUATION
Minimum starter conditions:
- close < 20DMA < 50DMA
- ADX >= 18
- RSI between 30 and 50
- 5-day return < 0

### 8.4 BEARISH_BREAKDOWN
Minimum starter conditions:
- close < 20DMA and close < 50DMA
- close below rolling 20-day low
- breakdown day volume >= 1.5x 20-day average volume
- ADX >= 16 or rising

### 8.5 Extension Rejection
A bullish setup is too extended if:
- close > 20DMA + 1.5 * ATR(14)

A bearish setup is too extended if:
- close < 20DMA - 1.5 * ATR(14)

If too extended:
- default outcome = NO_TRADE

---

## 9. Canonical IV Definition

### 9.1 Canonical implied volatility input
Use:
- 30-calendar-day ATM implied volatility proxy

If exact 30D ATM IV is unavailable:
1. choose nearest liquid expiry in target DTE neighborhood
2. choose strike nearest underlying price
3. use that IV as ATM proxy

### 9.2 IV Rank
- lookback = 252 trading days
- formula:
  `(current_iv - rolling_iv_min) / (rolling_iv_max - rolling_iv_min) * 100`

### 9.3 IV Rank denominator edge case
If:
- `rolling_iv_max == rolling_iv_min`

Then:
- set IV Rank = 50
- or mark unavailable and rely on IV/HV measures

### 9.4 Realized volatility
- HV window = 20 trading days
- annualized from daily log returns

### 9.5 IV/HV ratio
- `iv_30d_atm_proxy / hv_20`

### 9.6 IV-RV spread
- `iv_30d_atm_proxy - hv_20`

### 9.7 IV State Classification

#### IV_RICH
If one or more:
- IV Rank >= 60
- IV/HV >= 1.25
- IV - HV >= 5 vol points

#### IV_CHEAP
If:
- IV Rank <= 30
- IV/HV <= 1.05

#### IV_NORMAL
Otherwise

---

## 10. Expected Move Definitions

### 10.1 Implied move
Preferred:
- nearest target-DTE ATM straddle midpoint

Fallback:
- `underlying_price * iv_30d_atm_proxy * sqrt(dte / 365)`

### 10.2 Forecast move
Starter deterministic baseline:

#### Trend continuation forecast
- max(1.0 * ATR(14), simple realized-vol projection over intended holding horizon)

#### Breakout / breakdown forecast
- max(1.25 * ATR(14), 0.5 * breakout range height)

### 10.3 Structure interpretation
- if implied move materially exceeds forecast move and IV is rich -> credit spread preferred
- if forecast move is comparable to or exceeds implied move and IV is normal/cheap -> debit spread preferred

---

## 11. Event Risk Rules

### 11.1 Hard exclusion
Reject any trade if a scheduled earnings event occurs between:
- entry timestamp
- planned latest exit timestamp

### 11.2 Planned latest exit is deterministic

#### Credit spreads
Planned latest exit =
- `min(expiry - 7 calendar days, entry + 21 calendar days)`

#### Debit spreads
Planned latest exit =
- `min(expiry - 10 calendar days, entry + 14 calendar days)`

### 11.3 Additional caution buffer
Optional extra exclusion:
- reject if earnings occurs within 2 trading days after planned latest exit

### 11.4 Ex-dividend caution
If a short-call structure has:
- short call near-ITM or ITM
- ex-dividend before planned exit

then:
- flag for additional review or reject

For MVP this may be logged as caution if not yet enforced as hard exclusion.

---

## 12. Liquidity Qualification Rules

### 12.1 Underlying filters
- underlying price >= $20
- 20-day average stock volume >= 1,000,000 shares

### 12.2 Contract-level option filters
- open interest >= 500
- previous day volume >= 100, or rolling volume equivalent
- bid > 0
- ask > 0
- market not crossed
- bid/ask spread <= 8% of mid

### 12.3 Quote freshness
During market hours:
- underlying quote age <= 10 seconds
- option quote age <= 60 seconds

### 12.4 Spread-level quality
Both legs must independently pass filters.

Reject if:
- hedge leg is illiquid
- composite spread quality is poor
- one leg becomes non-actionable

---

## 13. Greek and Delta Sourcing Policy

Strike selection depends on delta.

### Priority order
1. use vendor Greeks if present and quote is fresh
2. if vendor Greeks missing, compute delta from midpoint-derived IV if supported
3. if delta cannot be sourced reliably, reject the contract

If strike targeting becomes unreliable:
- NO TRADE

---

## 14. Expiry Selection Rules

### 14.1 Credit spreads
Target DTE window:
- 25 to 45 calendar days

Select expiry by ranking:
1. best open interest near target delta
2. best bid/ask quality
3. nearest to 35 DTE

### 14.2 Debit spreads
Target DTE window:
- 14 to 45 calendar days

Select expiry by ranking:
1. best open interest near target long delta
2. best bid/ask quality
3. nearest to 28 DTE

### 14.3 Tie-break
If still tied:
- choose nearer expiry

### 14.4 Reject
If no expiry within target window passes liquidity rules:
- NO TRADE

---

## 15. Spread Width Policy

Spread width policy is a ceiling only.

> Actual spread width must use listed strikes available in the chain and the nearest compliant width not exceeding the policy cap.

### Width caps by underlying price
| Underlying Price | Target Width Ceiling |
|---|---:|
| $20 to $50 | $2.5 |
| $50 to $150 | $5 |
| $150+ | $5 |

Later versions may optionally allow wider spreads.

---

## 16. Strike Selection Rules

### 16.1 Bull Put Spread
Short put must satisfy:
- delta between 0.15 and 0.30
- liquidity rules
- support validity

Select short put by:
1. delta closest to 0.22
2. tighter bid/ask
3. higher OI

Long put hedge:
- next lower liquid listed strike
- width must not exceed policy cap

Support validity requires short put strike to be below:
- current underlying price
- 20DMA - 0.5 * ATR(14)
- recent 10-day swing low if available

### 16.2 Bear Call Spread
Short call must satisfy:
- delta between 0.15 and 0.30
- liquidity rules
- resistance validity

Select short call by:
1. delta closest to 0.22
2. tighter bid/ask
3. higher OI

Long call hedge:
- next higher liquid listed strike
- width must not exceed policy cap

Resistance validity requires short call strike to be above:
- current underlying price
- 20DMA + 0.5 * ATR(14)
- recent 10-day swing high if available

### 16.3 Bull Call Spread
Long call must satisfy:
- delta between 0.45 and 0.65
- liquidity rules

Select long call by:
1. delta closest to 0.55
2. tighter bid/ask
3. higher OI

Short call:
- choose listed strike near forecast target zone
- reward/risk must remain >= 1.0

### 16.4 Bear Put Spread
Long put must satisfy:
- absolute delta between 0.45 and 0.65
- liquidity rules

Select long put by:
1. delta closest to 0.55
2. tighter bid/ask
3. higher OI

Short put:
- choose listed strike near downside forecast target zone
- reward/risk must remain >= 1.0

### 16.5 Missing exact delta match
If exact target-delta strike does not exist:
- choose nearest liquid strike within +/- 0.03 delta
- otherwise choose nearest listed compliant liquid strike
- otherwise reject structure

---

## 17. Regime-to-Structure Mapping

| Market Regime | Underlying State | IV State | Preferred Structure | Secondary | Default |
|---|---|---|---|---|---|
| TREND_UP | BULLISH_CONTINUATION | IV_RICH | Bull Put Spread | Bull Call Spread | Candidate |
| TREND_UP | BULLISH_CONTINUATION | IV_NORMAL | Bull Call Spread | Bull Put Spread | Candidate |
| TREND_UP | BULLISH_CONTINUATION | IV_CHEAP | Bull Call Spread | None | Candidate |
| TREND_UP | BULLISH_BREAKOUT | IV_RICH | Bull Put Spread | Bull Call Spread | Candidate if not extended |
| TREND_UP | BULLISH_BREAKOUT | IV_NORMAL | Bull Call Spread | None | Candidate |
| TREND_UP | BULLISH_BREAKOUT | IV_CHEAP | Bull Call Spread | None | Candidate |
| TREND_DOWN | BEARISH_CONTINUATION | IV_RICH | Bear Call Spread | Bear Put Spread | Candidate |
| TREND_DOWN | BEARISH_CONTINUATION | IV_NORMAL | Bear Put Spread | Bear Call Spread | Candidate |
| TREND_DOWN | BEARISH_CONTINUATION | IV_CHEAP | Bear Put Spread | None | Candidate |
| TREND_DOWN | BEARISH_BREAKDOWN | IV_RICH | Bear Call Spread | Bear Put Spread | Candidate if not extended |
| TREND_DOWN | BEARISH_BREAKDOWN | IV_NORMAL | Bear Put Spread | None | Candidate |
| TREND_DOWN | BEARISH_BREAKDOWN | IV_CHEAP | Bear Put Spread | None | Candidate |
| Any | NEUTRAL | Any | None | None | NO TRADE |
| RANGE_UNCLEAR | Any | Any | None | None | NO TRADE |
| RISK_OFF | Any | Any | None | None | NO TRADE |
| SYSTEM_DEGRADED | Any | Any | None | None | NO TRADE |

---

## 18. Ranking Policy

### 18.1 Candidate scoring
Base score out of 100.

#### Components
- regime alignment: 0 to 20
- directional strength: 0 to 25
- IV/structure fit: 0 to 20
- liquidity quality: 0 to 20
- expected move fit: 0 to 15

#### Penalties
- extension penalty: -10
- event caution penalty: -15
- portfolio conflict penalty: -20
- sector concentration warning: -10

### 18.2 Hard rejection
Reject if:
- score < 70
- event exclusion violated
- liquidity fails
- regime permission violated
- system degraded
- no valid structure constructed

### 18.3 Final selection
After scoring:
1. sort descending by score
2. apply portfolio caps
3. select top N

### 18.4 Tie-break order
1. higher total score
2. better liquidity quality
3. better expected move fit
4. lower event risk
5. better diversification contribution

---

## 19. Position Sizing

### 19.1 Credit spread max risk
- spread width - credit received

### 19.2 Debit spread max risk
- debit paid

### 19.3 Account-level policy
- per-trade max risk = 1.0% of account equity
- max open positions = 5
- max same-direction share = 60% of open slots
- max per underlying = 1
- max per sector = 2

No averaging down.

---

## 20. Entry Timing Policy

MVP operating windows:
- nightly signal generation
- pre-market qualification
- scheduled intraday execution windows

Suggested intraday windows:
- 10:30 ET
- 13:00 ET
- 15:00 ET

No continuous reactive execution in MVP.

---

## 21. Execution Policy

### 21.1 Order type
- all entries are limit combo orders
- no market orders
- no manual legging by default

### 21.2 Entry pricing
Credit spreads:
- start at modeled fair credit = mid - slippage buffer

Debit spreads:
- start at modeled fair debit = mid + slippage buffer

### 21.3 Repricing
- max 3 repricing attempts
- max 5 minutes total
- never exceed max slippage budget

### 21.4 Slippage budget
MVP default:
- no more than 10% adverse relative to modeled mid

### 21.5 Reject / no fill
If not filled after repricing policy:
- mark signal as NO FILL / EXPIRED SIGNAL

Reject if:
- spread widens materially
- quote quality degrades
- one leg loses liquidity
- underlying moves beyond entry tolerance

---

## 22. Lifecycle States

### 22.1 Signal states
- CANDIDATE
- QUALIFIED
- REJECTED
- EXPIRED

### 22.2 Order states
- ORDER_DRAFTED
- ORDER_SUBMITTED
- PARTIALLY_FILLED
- FILLED
- CANCELED
- REJECTED

### 22.3 Position states
- OPEN
- EXIT_PENDING
- CLOSED

---

## 23. Exit Rules

### 23.1 Credit spreads
Profit target:
- 50% of max credit captured

Hard loss / invalidation:
- spread value reaches 2x entry credit
- thesis invalidated technically
- risk shock materially changes context

Time exit:
- exit at 7 DTE

### 23.2 Debit spreads
Profit target:
- baseline target = 50% of max attainable spread profit opportunity
- may also respect technical target logic

Loss / invalidation:
- spread loses 50% of entry debit
- technical thesis fails

Time exit:
- exit at 10 DTE

---

## 24. Exit Priority Ordering

When multiple exits trigger, order is:

1. SYSTEM / OPS EMERGENCY EXIT
2. EVENT EXIT
3. HARD LOSS / TECHNICAL INVALIDATION
4. TIME EXIT
5. PROFIT TARGET

This ordering must be consistent in monitoring logic.

---

## 25. Monitoring Cadence

MVP evaluation cadence:
- after close
- before market
- scheduled intraday windows only

No continuous tick-level monitoring in MVP.

---

## 26. Default No-Trade Conditions

NO TRADE if any:
- regime not permitted
- directional signal weak/conflicted
- setup overextended
- event exclusion violated
- no valid expiry
- no valid strikes
- liquidity insufficient
- quote stale
- expected move relation not supportive
- portfolio limits breached
- system degraded

---

## 27. Build-Against Statement

This rulebook is approved for:

- deterministic candidate generation
- structure construction logic
- invariant testing
- paper strategy development
- backtest specification
- Phase 1 implementation

It is not yet approval for unattended live trading.
