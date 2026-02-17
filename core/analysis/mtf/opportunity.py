from dataclasses import dataclass
from typing import Dict


@dataclass
class ScoreBreakdown:
    alignment: int = 0
    structural_bonus: int = 0
    momentum: int = 0


@dataclass
class OpportunityScore:
    grade: str
    total_score: int
    context: str  # continuation / reversal
    breakdown: ScoreBreakdown


def score_to_grade(score: int) -> str:
    if score >= 9:
        return "A+"
    elif score >= 6:
        return "A"
    elif score >= 4:
        return "B"
    return "C"


def calculate_alignment_score(weekly, daily, h4, m15):
    score = 0

    if daily.bias.external == weekly.bias.external:
        score += 3

    if h4.bias.external == daily.bias.external:
        score += 2

    if m15.bias.external == h4.bias.external:
        score += 1

    return score


def calculate_structural_bonus(snapshot, dominant_bias):
    bonus = 0

    state = snapshot.state

    if dominant_bias == "bullish":
        if state == "bullish_correction":
            bonus += 2
        elif state == "bullish_expansion":
            bonus += 1

    elif dominant_bias == "bearish":
        if state == "bearish_correction":
            bonus += 2
        elif state == "bearish_expansion":
            bonus += 1

    return bonus


def calculate_momentum_score(momentum, dominant_bias):
    if dominant_bias == "bullish":
        if momentum > 0:
            return 2
        elif momentum == 0:
            return 1
        return 0

    if dominant_bias == "bearish":
        if momentum < 0:
            return 2
        elif momentum == 0:
            return 1
        return 0

    return 0


def build_continuation_score(weekly, daily, h4, m15):
    dominant_bias = weekly.bias.external or daily.bias.external

    breakdown = ScoreBreakdown()

    # Alignment
    breakdown.alignment = calculate_alignment_score(weekly, daily, h4, m15)

    # Structural bonus uses H4 context primarily
    breakdown.structural_bonus = calculate_structural_bonus(h4, dominant_bias)

    # Momentum uses entry timeframe
    breakdown.momentum = calculate_momentum_score(m15.momentum, dominant_bias)

    total = breakdown.alignment + breakdown.structural_bonus + breakdown.momentum

    return OpportunityScore(
        grade=score_to_grade(total),
        total_score=total,
        context="continuation",
        breakdown=breakdown,
    )


def build_reversal_score(weekly, daily, h4, m15):
    breakdown = ScoreBreakdown()

    # Reversal bias driven by DAILY vs WEEKLY conflict
    reversal_pressure = 0

    if daily.bias.external and weekly.bias.external:
        if daily.bias.external != weekly.bias.external:
            reversal_pressure += 3

    if h4.bias.external == daily.bias.external:
        reversal_pressure += 2

    if m15.bias.external == h4.bias.external:
        reversal_pressure += 1

    breakdown.alignment = reversal_pressure

    # Momentum supporting reversal direction
    reversal_bias = daily.bias.external

    breakdown.momentum = calculate_momentum_score(m15.momentum, reversal_bias)

    total = breakdown.alignment + breakdown.momentum

    return OpportunityScore(
        grade=score_to_grade(total),
        total_score=total,
        context="reversal",
        breakdown=breakdown,
    )


@dataclass
class OpportunitySnapshot:
    continuation: OpportunityScore
    reversal: OpportunityScore


def build_opportunity_snapshot(weekly, daily, h4, m15):

    continuation = build_continuation_score(weekly, daily, h4, m15)

    reversal = build_reversal_score(weekly, daily, h4, m15)

    return OpportunitySnapshot(continuation=continuation, reversal=reversal)


def grade_trade_setup(
    structure_aligned: bool,
    momentum_score: int,
    zone_quality: str,
    liquidity_signal: bool,
    entry_confirmation: bool,
):
    breakdown = {
        "structure_alignment": 0,
        "momentum_confirmation": 0,
        "supply_demand_quality": 0,
        "liquidity_context": 0,
        "entry_refinement": 0,
    }

    total_score = 0

    # -------------------------
    # Structure Alignment
    # -------------------------
    if structure_aligned:
        breakdown["structure_alignment"] = 2
        total_score += 2

    # -------------------------
    # Momentum Confirmation
    # -------------------------
    if momentum_score >= 2:
        breakdown["momentum_confirmation"] = 2
        total_score += 2
    elif momentum_score == 1:
        breakdown["momentum_confirmation"] = 1
        total_score += 1

    # -------------------------
    # Supply/Demand Quality
    # -------------------------
    if zone_quality == "fresh":
        breakdown["supply_demand_quality"] = 2
        total_score += 2
    elif zone_quality == "tested":
        breakdown["supply_demand_quality"] = 1
        total_score += 1

    # -------------------------
    # Liquidity Context
    # -------------------------
    if liquidity_signal:
        breakdown["liquidity_context"] = 1
        total_score += 1

    # -------------------------
    # Entry Confirmation
    # -------------------------
    if entry_confirmation:
        breakdown["entry_refinement"] = 1
        total_score += 1

    # -------------------------
    # Grade Assignment
    # -------------------------
    if total_score >= 7:
        grade = "A+"
    elif total_score >= 5:
        grade = "A"
    elif total_score >= 3:
        grade = "B"
    else:
        grade = "Avoid"

    return {"grade": grade, "score": total_score, "breakdown": breakdown}
