from freqtrade.papertrade.types import Direction, EngineState, ExitReason, OrderStatus


class TestTypes:

    def test_direction_values(self):
        assert Direction.LONG.value == "long"
        assert Direction.SHORT.value == "short"
        assert Direction.NO_TRADE.value == "no_trade"

    def test_engine_states(self):
        assert EngineState.RUNNING.value == "running"
        assert EngineState.STOPPED.value == "stopped"

    def test_order_status(self):
        assert OrderStatus.CREATED.value == "created"
        assert OrderStatus.FILLED.value == "filled"
        assert OrderStatus.CANCELLED.value == "cancelled"

    def test_exit_reasons(self):
        assert ExitReason.STOP_LOSS.value == "stop_loss"
        assert ExitReason.MAX_HOLD.value == "max_hold"
        assert ExitReason.OPPOSITE_SIGNAL.value == "opposite_signal"
