from dataclasses import dataclass


@dataclass
class Setup:
    symbol: str
    direction: str  # 'bullish' / 'bearish'
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence_score: int
