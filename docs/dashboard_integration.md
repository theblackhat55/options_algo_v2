# Dashboard Integration

This repository produces data artifacts consumed directly by the shared `trading_dashboard` repository.

## Primary data directories

### Scan artifacts
- `data/scan_results/scan_*.json`

These contain:
- `run_id`
- `generated_at`
- `summary`
- `runtime_metadata`
- `decisions`
- `trade_candidates`
- `trade_ideas`
- `feature_sources`

### Paper-live validation logs
- `data/validation/paper_live_runs.jsonl`
- `data/validation/paper_live_symbol_decisions.jsonl`
- `data/validation/paper_live_runs.csv`

These support:
- run history
- pass/reject trends
- symbol leaderboard analysis
- rejection reason distributions

### State
- `data/state/iv_proxy_history.jsonl`

This supports:
- IV proxy history by symbol
- IV-rank readiness tracking
- observation count monitoring

## Runtime metadata fields used by dashboard

The dashboard may consume these fields from latest scan runtime metadata:

- `runtime_mode`
- `as_of_date`
- `strict_live_mode`
- `degraded_live_mode`
- `used_placeholder_iv_inputs`
- `used_placeholder_iv_rank_inputs`
- `used_placeholder_iv_hv_ratio_inputs`
- `used_placeholder_liquidity_inputs`
- `iv_rank_ready_symbols`
- `iv_rank_insufficient_history_symbols`
- `iv_rank_observation_count_by_symbol`
- `aggregate_quote_quality_counts`
- `quote_quality_by_symbol`
- `liquidity_debug_by_symbol`
- `top_trade_candidate_symbols`
- `trade_idea_count`
- `trade_idea_symbols`

## Integration model

- Dashboard code lives in the `trading_dashboard` repository.
- This repository only produces filesystem artifacts under `data/...`.
- The dashboard reads these files directly from the local filesystem.
