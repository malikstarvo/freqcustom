

class DecayResult:
    def __init__(self, peak_corr: float = 0.0, avg_corr: float = 0.0,
                 decay_rate: float = 0.0, persistence: float = 0.0) -> None:
        self.peak_corr = peak_corr
        self.avg_corr = avg_corr
        self.decay_rate = decay_rate
        self.persistence = persistence


def analyze_decay(correlations: list[float]) -> DecayResult:
    abs_corrs = [abs(c) for c in correlations]

    if len(abs_corrs) == 0:
        return DecayResult()

    peak = abs_corrs[0]
    corr_sum = abs_corrs[0]
    for i in range(1, len(abs_corrs)):
        if abs_corrs[i] > peak:
            peak = abs_corrs[i]
        corr_sum += abs_corrs[i]
    avg_corr = corr_sum / len(abs_corrs)

    decay_rate = 0.0
    if len(abs_corrs) >= 2:
        decay_rate = (abs_corrs[0] - abs_corrs[-1]) / (len(abs_corrs) - 1)

    persistence = abs_corrs[0]
    for c in abs_corrs:
        if c < persistence:
            persistence = c

    return DecayResult(
        peak_corr=peak, avg_corr=avg_corr,
        decay_rate=decay_rate, persistence=persistence,
    )
