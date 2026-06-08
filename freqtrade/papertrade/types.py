from enum import Enum


class Direction(str, Enum):  # noqa: UP042
    LONG = "long"
    SHORT = "short"
    NO_TRADE = "no_trade"


class EngineState(str, Enum):  # noqa: UP042
    RUNNING = "running"
    STOPPED = "stopped"


class OrderStatus(str, Enum):  # noqa: UP042
    CREATED = "created"
    FILLED = "filled"
    CANCELLED = "cancelled"


class ExitReason(str, Enum):  # noqa: UP042
    STOP_LOSS = "stop_loss"
    MAX_HOLD = "max_hold"
    OPPOSITE_SIGNAL = "opposite_signal"
    END_OF_DATA = "end_of_data"
    DRAWDOWN_DAILY = "drawdown_daily"
