# Strategy

## System Definition
`options_algo_v2` is a rule-based options structure-selection engine that maps:

- market regime
- underlying directional state
- implied volatility state
- liquidity quality
- event risk
- portfolio constraints

into defined-risk vertical spread trade candidates.

## MVP Scope
The MVP supports only four strategy types:

### Premium-selling family
- Bull Put Spread
- Bear Call Spread

### Directional debit family
- Bull Call Spread
- Bear Put Spread

## Deferred Strategies
The following are intentionally out of MVP scope:

- Long Call
- Long Put
- Iron Condor
- Butterfly
- Calendar / Diagonal structures
- Rolling / adjustment logic

## Strategy Philosophy
The same directional view should not always be expressed with the same structure.

Examples:

- a bullish setup in rich IV may be better expressed as a Bull Put Spread
- a bullish setup in cheap/normal IV may be better expressed as a Bull Call Spread
- a bearish setup in rich IV may be better expressed as a Bear Call Spread
- a bearish setup in cheap/normal IV may be better expressed as a Bear Put Spread

This is the core structure-selection logic behind the system.

## Edge Hypotheses

### Hypothesis A: Credit spread edge
When:

- the directional setup is aligned,
- implied volatility is elevated relative to realized volatility,
- the implied move is larger than the system’s forecast move,
- the options chain is liquid,
- and no binary event lies inside the holding window,

then defined-risk credit spreads should have positive expectancy after costs.

### Hypothesis B: Debit spread edge
When:

- the directional setup is strong,
- implied volatility is not elevated,
- the expected move is meaningful,
- the chain is liquid,
- and event risk is controlled,

then defined-risk debit spreads should outperform credit spreads as the directional expression.

### Hypothesis C: Structure adaptation edge
A directional thesis expressed through the structure most appropriate to IV and expected move conditions should outperform a single-structure-only policy.

## Decision Layers

### Layer 1: Market regime
The system determines whether the market supports bullish, bearish, or no new directional entries.

Outputs:

- TREND_UP
- TREND_DOWN
- RANGE_UNCLEAR
- RISK_OFF

### Layer 2: Underlying directional state
Each symbol is classified into:

- BULLISH_CONTINUATION
- BULLISH_BREAKOUT
- BEARISH_CONTINUATION
- BEARISH_BREAKDOWN
- NEUTRAL
- NO_TRADE

### Layer 3: IV state
Each symbol is assigned:

- IV_RICH
- IV_NORMAL
- IV_CHEAP

### Layer 4: Liquidity and event qualification
Only candidates with acceptable chain quality and no disqualifying event risk survive.

### Layer 5: Structure selection and ranking
The candidate is mapped to a preferred vertical spread and scored.

## Universe Definition
The MVP should trade a fixed, versioned universe of liquid US equities and ETFs.

Universe membership should be frozen per rulebook/config version to preserve research reproducibility.

Examples of suitable universe members:

- SPY, QQQ, IWM
- XLK, XLF, XLE, SMH
- AAPL, MSFT, NVDA, AMZN, META, GOOGL, AMD, TSLA, JPM, BAC, XOM, CVX

## Universe Constraints
Eligible names must generally satisfy:

- stock price >= $20
- sufficiently liquid stock and options market
- stable options chain quality
- no persistent chain anomalies

## Market Regime Philosophy

### TREND_UP
Only bullish structures are eligible.

### TREND_DOWN
Only bearish structures are eligible.

### RANGE_UNCLEAR
No new directional entries in MVP.

### RISK_OFF
No new entries in MVP.

This is intentionally strict.

## Underlying Setup Philosophy

### Bullish continuation
Used for trend-following bullish conditions where trend is intact and not excessively extended.

### Bullish breakout
Used for directional upside expansion setups where range resolution is confirmed.

### Bearish continuation
Used for persistent downside trend setups.

### Bearish breakdown
Used for downside expansion setups.

### Neutral / No-trade
If the setup is mixed, overextended, poorly aligned, or otherwise low quality, the system does nothing.

## IV-State Philosophy

### IV_RICH
Supports premium-selling preference when directional alignment exists.

### IV_NORMAL / IV_CHEAP
Supports debit spread preference when directional continuation or breakout conditions exist.

## Expected Move Logic
The system compares:

- implied move from the options market
- forecast move from a simple deterministic model

This comparison helps decide whether premium selling or premium buying via spreads is more appropriate.

## Strategy Mapping

### Bullish + IV_RICH
Preferred:
- Bull Put Spread

Secondary:
- Bull Call Spread

### Bullish + IV_NORMAL / IV_CHEAP
Preferred:
- Bull Call Spread

### Bearish + IV_RICH
Preferred:
- Bear Call Spread

Secondary:
- Bear Put Spread

### Bearish + IV_NORMAL / IV_CHEAP
Preferred:
- Bear Put Spread

## Why Vertical Spreads for MVP
Vertical spreads are chosen for MVP because they are:

- defined risk
- easier to simulate than complex structures
- easier to monitor than multi-wing structures
- more robust for early productionization
- sufficient to test the core edge hypotheses

## Event Philosophy
The system does not attempt to capture event premium in MVP.

If an earnings event lies inside the intended holding window, the trade is rejected.

## Risk Philosophy
The system values:

- capped downside
- consistent sizing
- portfolio concentration limits
- no forced trades
- no rolling rescue logic
- explicit exits

## What Success Means Strategically
The strategy is working if the system can demonstrate:

- better expectancy than a naive one-structure policy
- improved risk-adjusted outcomes through structure adaptation
- fewer bad entries caused by poor IV context or poor chain quality
- cleaner paper-trade lifecycle behavior with explicit exits

## Future Strategy Expansion
If the MVP proves robust, later versions may expand to:

- long premium outright trades
- neutral structures
- more nuanced regime handling
- portfolio-level Greek optimization
- ML-enhanced ranking and filtering

But those are intentionally deferred until the deterministic baseline proves itself.
