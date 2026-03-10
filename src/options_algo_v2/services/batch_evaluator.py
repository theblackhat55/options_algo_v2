from __future__ import annotations

from options_algo_v2.domain.decision import CandidateDecision
from options_algo_v2.domain.raw_features import RawFeatureInput
from options_algo_v2.services.feature_normalizer import (
    normalize_raw_features_to_payload,
)
from options_algo_v2.services.pipeline_evaluator import evaluate_pipeline_payload


def evaluate_raw_feature_batch(
    raw_features: list[RawFeatureInput],
) -> list[CandidateDecision]:
    decisions: list[CandidateDecision] = []

    for raw in raw_features:
        payload = normalize_raw_features_to_payload(raw)
        decision = evaluate_pipeline_payload(payload)
        decisions.append(decision)

    return decisions
