from __future__ import annotations

from pprint import pprint

from options_algo_v2.domain.candidates import StrategyCandidate
from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.enums import (
    DirectionalState,
    IVState,
    MarketRegime,
    SignalState,
    StrategyType,
)
from options_algo_v2.domain.options_chain import OptionQuote, OptionsChainSnapshot
from options_algo_v2.domain.qualification import QualificationResult
from options_algo_v2.services.single_leg_trade_candidates import (
    select_single_leg_trade_candidates,
)

passed = QualificationResult(passed=True, reasons=[])

candidate = StrategyCandidate(
    symbol="NFLX",
    market_regime=MarketRegime.TREND_UP,
    directional_state=DirectionalState.BULLISH_BREAKOUT,
    iv_state=IVState.IV_NORMAL,
    strategy_type=StrategyType.LONG_CALL,
    signal_state=SignalState.QUALIFIED,
    score=0.0,
    rationale=[
        "market_regime=TREND_UP",
        "directional_state=BULLISH_BREAKOUT",
        "iv_state=IV_NORMAL",
        "selected_strategy=LONG_CALL",
        "eligible_strategies=BULL_CALL_SPREAD,LONG_CALL",
        "long_call_alternative_eligible",
    ],
)

decision = CandidateDecision(
    candidate=candidate,
    event_result=passed,
    liquidity_result=passed,
    extension_result=passed,
    final_passed=False,
    final_score=69.0,
    min_score_required=70.0,
    underlying_price=950.0,
    avg_daily_volume=1000000.0,
    option_open_interest=500,
    option_volume=50,
    bid=1.20,
    ask=1.30,
    close=950.0,
    dma20=940.0,
    dma50=930.0,
    atr20=18.0,
    adx14=28.0,
    iv_rank=35.0,
    iv_hv_ratio=1.02,
    market_breadth_pct_above_20dma=58.0,
)

chain = OptionsChainSnapshot(
    symbol="NFLX",
    as_of="2026-04-16T00:00:00Z",
    source="test",
    quotes=[
        OptionQuote(
            symbol="NFLX",
            option_symbol="NFLX_CALL_960_20260515",
            expiration="2026-05-15",
            strike=960.0,
            option_type="CALL",
            bid=3.00,
            ask=3.20,
            mid=3.10,
            delta=0.52,
            implied_volatility=0.32,
            open_interest=4500,
            volume=1200,
        ),
        OptionQuote(
            symbol="NFLX",
            option_symbol="NFLX_CALL_970_20260515",
            expiration="2026-05-15",
            strike=970.0,
            option_type="CALL",
            bid=2.10,
            ask=2.35,
            mid=2.225,
            delta=0.47,
            implied_volatility=0.31,
            open_interest=4200,
            volume=1100,
        ),
        OptionQuote(
            symbol="NFLX",
            option_symbol="NFLX_PUT_940_20260515",
            expiration="2026-05-15",
            strike=940.0,
            option_type="PUT",
            bid=2.90,
            ask=3.10,
            mid=3.00,
            delta=-0.48,
            implied_volatility=0.33,
            open_interest=3000,
            volume=900,
        ),
    ],
)

items = select_single_leg_trade_candidates(
    decision=decision,
    chain=chain,
    as_of_date=__import__("datetime").date(2026, 4, 16),
)

print("single-leg candidates:")
pprint(items)
