# Watchlist Design

## Purpose
Build a broader market prefilter before running the v2 options strategy.

The watchlist should answer:
1. Which underlyings are interesting?
2. Which underlyings are option-tradeable today?
3. Which symbols deserve full options-chain strategy evaluation?

## Current implementation (as of 2026-03-22)

The watchlist pipeline is fully operational:

```
build_watchlist.py → build_options_watchlist.py → filter_options_watchlist.py → run_paper_live_daily.py
```

- `scripts/build_watchlist.py` — builds underlying interest watchlist from the universe
- `scripts/build_options_watchlist.py` — adds Polygon options viability data per symbol
- `scripts/filter_options_watchlist.py` — filters to symbols with viable options today
- Filtered watchlist JSON is passed to the scan scripts via `--watchlist`

The fixed universe is 58 symbols across all 11 GICS sectors (`config/universe_v1.yaml`).

---

## Stage 1: Underlying Watchlist
### Inputs
- Databento daily OHLCV bars
- Market breadth/regime
- Universe symbols

### Suggested Filters
- minimum price
- minimum average daily volume
- minimum average dollar volume
- trend strength
- momentum / directional strength
- ATR / volatility floor
- extension distance from moving average
- breadth alignment

### Suggested Output Fields
- symbol
- watchlist_score
- price
- avg_volume
- avg_dollar_volume
- adx14
- price_vs_20dma_pct
- iv_context if available
- directional_state_preliminary
- regime_alignment
- reason_codes

---

## Stage 2: Options Viability Screen
### Inputs
- Stage 1 watchlist symbols
- Polygon option chain snapshots

### Suggested Filters
- minimum total options volume
- minimum open interest
- maximum bid/ask width
- minimum count of viable contracts near target DTE
- minimum count of real quotes
- synthetic quote fraction
- zero-delta / missing-greeks diagnostics

### Suggested Output Fields
- symbol
- options_viable
- options_volume_total
- open_interest_total
- contracts_with_real_quotes
- contracts_with_acceptable_spread
- contracts_near_target_dte
- synthetic_quote_count
- missing_greeks_count
- viability_score
- reason_codes

---

## Combined Watchlist Philosophy
The final watchlist should be:
- underlying-interesting
- options-tradeable
- aligned with current market regime

Not every technically strong stock is options-tradeable.
Not every active options name is a good underlying setup.

---

## Rollout Plan
1. Start with liquid universe only
2. Build watchlist JSON output
3. Add options viability scoring
4. Feed resulting symbols into run_nightly_scan
5. Expand universe after stability is proven
