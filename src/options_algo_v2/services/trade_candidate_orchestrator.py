from __future__ import annotations

from datetime import date
from typing import Any

from options_algo_v2.config.rulebook_config import load_rulebook_configs
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.options_chain_provider import OptionsChainProvider
from options_algo_v2.domain.trade_candidate import TradeCandidate
from options_algo_v2.services.decision_spread_mapper import get_target_spread_family
from options_algo_v2.services.expiration_aware_spread_selector import (
    select_spread_candidates_across_expirations,
)
from options_algo_v2.services.qualified_trade_candidate_builder import (
    build_qualified_trade_candidates,
)
from options_algo_v2.services.runtime_execution_settings import (
    get_runtime_execution_settings,
)


def _load_strategy_config() -> dict[str, Any]:
    """Load strategy_v1.yaml and return it as a dict."""
    try:
        configs = load_rulebook_configs()
        return configs.strategy
    except Exception:
        return {}


def build_trade_candidates_for_decision(
    *,
    decision: CandidateDecision,
    options_chain_provider: OptionsChainProvider,
    expiration: str,
    min_open_interest: int,
    max_bid_ask_spread_width: float,
    as_of_date: date | None = None,
) -> list[TradeCandidate]:
    _ = expiration
    execution_settings = get_runtime_execution_settings()
    resolved_as_of_date = (
        as_of_date or execution_settings.as_of_date
    )
    chain = options_chain_provider.get_chain(symbol=decision.candidate.symbol)

    # Resolve DTE and delta parameters from strategy config
    strategy = _load_strategy_config()
    family = get_target_spread_family(decision)
    is_credit = family in ("BULL_PUT_SPREAD", "BEAR_CALL_SPREAD")

    if is_credit:
        min_dte = int(strategy.get("credit_spread_dte_min", 25))
        target_dte = int(strategy.get("credit_spread_dte_target", 35))
        max_dte = int(strategy.get("credit_spread_dte_max", 45))
    else:
        min_dte = int(strategy.get("debit_spread_dte_min", 14))
        target_dte = int(strategy.get("debit_spread_dte_target", 28))
        max_dte = int(strategy.get("debit_spread_dte_max", 45))

    credit_short_delta_min = float(strategy.get("credit_short_delta_min", 0.15))
    credit_short_delta_max = float(strategy.get("credit_short_delta_max", 0.30))
    debit_long_delta_min = float(strategy.get("debit_long_delta_min", 0.45))
    debit_long_delta_max = float(strategy.get("debit_long_delta_max", 0.65))

    spread_candidates = select_spread_candidates_across_expirations(
        decision=decision,
        chain=chain,
        as_of_date=resolved_as_of_date,
        min_dte=min_dte,
        max_dte=max_dte,
        target_dte=target_dte,
        credit_short_delta_min=credit_short_delta_min,
        credit_short_delta_max=credit_short_delta_max,
        debit_long_delta_min=debit_long_delta_min,
        debit_long_delta_max=debit_long_delta_max,
    )

    if not spread_candidates and execution_settings.allow_short_dte_fallback:
        spread_candidates = select_spread_candidates_across_expirations(
            decision=decision,
            chain=chain,
            as_of_date=resolved_as_of_date,
            min_dte=1,
            max_dte=14,
            target_dte=7,
            credit_short_delta_min=credit_short_delta_min,
            credit_short_delta_max=credit_short_delta_max,
            debit_long_delta_min=debit_long_delta_min,
            debit_long_delta_max=debit_long_delta_max,
        )

    return build_qualified_trade_candidates(
        spread_candidates,
        min_open_interest=min_open_interest,
        max_bid_ask_spread_width=max_bid_ask_spread_width,
    )
