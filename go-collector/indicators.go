package main

import "math"

type IndicatorStore struct {
	prices   []float64
	volumes  []float64
	highs    []float64
	lows     []float64
	ema20    float64
	ema50    float64
	ema200   float64
}

func NewIndicatorStore() *IndicatorStore {
	return &IndicatorStore{}
}

func (is *IndicatorStore) AddCandle(open, high, low, close, volume float64) {
	is.prices = append(is.prices, close)
	is.volumes = append(is.volumes, volume)
	is.highs = append(is.highs, high)
	is.lows = append(is.lows, low)

	if len(is.prices) > 200 {
		is.prices = is.prices[1:]
		is.volumes = is.volumes[1:]
		is.highs = is.highs[1:]
		is.lows = is.lows[1:]
	}

	is.ema20 = is.computeEMA(20)
	is.ema50 = is.computeEMA(50)
	is.ema200 = is.computeEMA(200)
}

func (is *IndicatorStore) computeEMA(period int) float64 {
	n := len(is.prices)
	if n < period {
		if n == 0 {
			return 0
		}
		return is.prices[n-1]
	}
	k := 2.0 / float64(period+1)
	ema := is.prices[0]
	for _, p := range is.prices[1:] {
		ema = p*k + ema*(1-k)
	}
	return ema
}

func (is *IndicatorStore) EMAs() (float64, float64, float64) {
	return is.ema20, is.ema50, is.ema200
}

func (is *IndicatorStore) RSI(period int) float64 {
	n := len(is.prices)
	if n < period+1 {
		return 50.0
	}
	gainTotal := 0.0
	lossTotal := 0.0
	for i := n - period; i < n; i++ {
		delta := is.prices[i] - is.prices[i-1]
		if delta > 0 {
			gainTotal += delta
		} else {
			lossTotal -= delta
		}
	}
	avgGain := gainTotal / float64(period)
	avgLoss := lossTotal / float64(period)
	if avgLoss == 0 {
		return 100.0
	}
	rs := avgGain / avgLoss
	return 100.0 - (100.0 / (1.0 + rs))
}

func (is *IndicatorStore) ATR(period int) float64 {
	n := len(is.prices)
	if n < period+1 {
		return 0
	}
	sum := 0.0
	for i := n - period; i < n; i++ {
		tr := math.Max(is.highs[i]-is.lows[i],
			math.Max(math.Abs(is.highs[i]-is.prices[i-1]),
				math.Abs(is.lows[i]-is.prices[i-1])))
		sum += tr
	}
	return sum / float64(period)
}

func (is *IndicatorStore) ADX(period int) float64 {
	n := len(is.prices)
	if n < period*2 {
		return 0
	}
	trSum := 0.0
	pDMSum := 0.0
	nDMSum := 0.0
	for i := n - period; i < n; i++ {
		tr := math.Max(is.highs[i]-is.lows[i],
			math.Max(math.Abs(is.highs[i]-is.prices[i-1]),
				math.Abs(is.lows[i]-is.prices[i-1])))
		upMove := is.highs[i] - is.highs[i-1]
		downMove := is.lows[i-1] - is.lows[i]
		pDM := 0.0
		nDM := 0.0
		if upMove > downMove && upMove > 0 {
			pDM = upMove
		}
		if downMove > upMove && downMove > 0 {
			nDM = downMove
		}
		trSum += tr
		pDMSum += pDM
		nDMSum += nDM
	}
	if trSum == 0 {
		return 0
	}
	pDI := (pDMSum / trSum) * 100
	nDI := (nDMSum / trSum) * 100
	dxSum := pDI + nDI
	if dxSum == 0 {
		return 0
	}
	return math.Abs(pDI-nDI) / dxSum * 100
}

func (is *IndicatorStore) VolumeEMA(period int) float64 {
	n := len(is.volumes)
	if n < period {
		if n == 0 {
			return 0
		}
		return is.volumes[n-1]
	}
	k := 2.0 / float64(period+1)
	ema := is.volumes[0]
	for _, v := range is.volumes[1:] {
		ema = v*k + ema*(1-k)
	}
	return ema
}

func (is *IndicatorStore) Volatility(period int) float64 {
	n := len(is.prices)
	if n < period+1 {
		return 0
	}
	sum := 0.0
	count := 0
	for i := n - period; i < n; i++ {
		if is.prices[i-1] > 0 {
			ret := (is.prices[i] - is.prices[i-1]) / is.prices[i-1]
			sum += ret * ret
			count++
		}
	}
	if count == 0 {
		return 0
	}
	return math.Sqrt(sum/float64(count)) * 100
}
