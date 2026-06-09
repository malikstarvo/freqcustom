package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"strconv"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/shopspring/decimal"
)

const bybitWSURL = "wss://stream.bybit.com/v5/public/linear"

type BybitClient struct {
	Symbol     string
	Timeframes []string

	prices map[string]*IndicatorStore
	mu     sync.Mutex

	fundingRate decimal.Decimal
	oiDeltaPct  decimal.Decimal
	lsRatio     decimal.Decimal
	liqLong     decimal.Decimal
	liqShort    decimal.Decimal
}

func NewBybitClient(symbol string, timeframes []string) *BybitClient {
	p := make(map[string]*IndicatorStore)
	for _, tf := range timeframes {
		p[tf] = NewIndicatorStore()
	}
	return &BybitClient{
		Symbol:     symbol,
		Timeframes: timeframes,
		prices:     p,
	}
}

type wsSubscription struct {
	Op   string   `json:"op"`
	Args []string `json:"args"`
}

func (c *BybitClient) Stream(db *TimescaleStore, featureSetID int) {
	for {
		err := c.connect(db, featureSetID)
		if err != nil {
			log.Printf("[%s] WS error: %v, reconnecting in 5s...", c.Symbol, err)
			time.Sleep(5 * time.Second)
		}
	}
}

func (c *BybitClient) connect(db *TimescaleStore, featureSetID int) error {
	conn, _, err := websocket.DefaultDialer.Dial(bybitWSURL, nil)
	if err != nil {
		return err
	}
	defer conn.Close()

	// Subscribe: kline for each timeframe
	args := make([]string, 0)
	for _, tf := range c.Timeframes {
		args = append(args, fmt.Sprintf("kline.%s.%s", tf, c.Symbol))
	}
	args = append(args,
		fmt.Sprintf("tickers.%s", c.Symbol),
		fmt.Sprintf("open_interest.%s", c.Symbol),
		fmt.Sprintf("liquidation.%s", c.Symbol),
	)

	sub := wsSubscription{Op: "subscribe", Args: args}
	if err := conn.WriteJSON(sub); err != nil {
		return err
	}
	log.Printf("[%s] Subscribed: %v", c.Symbol, args)

	// Heartbeat: ping every 20 seconds to keep connection alive
	done := make(chan struct{})
	defer close(done)
	go func() {
		ticker := time.NewTicker(20 * time.Second)
		defer ticker.Stop()
		for {
			select {
			case <-ticker.C:
				conn.WriteJSON(wsSubscription{Op: "ping"})
			case <-done:
				return
			}
		}
	}()

	for {
		_, msg, err := conn.ReadMessage()
		if err != nil {
			return err
		}
		c.handleMessage(msg, db, featureSetID)
	}
}

type wsBaseMsg struct {
	Topic string `json:"topic"`
	Type  string `json:"type"`
}

type klineMsg struct {
	Topic string     `json:"topic"`
	Data  []klineBar `json:"data"`
}

type klineBar struct {
	Start  string `json:"start"`
	Open   string `json:"open"`
	High   string `json:"high"`
	Low    string `json:"low"`
	Close  string `json:"close"`
	Volume string `json:"volume"`
	Confirm bool  `json:"confirm"`
}

func (c *BybitClient) handleMessage(raw []byte, db *TimescaleStore, featureSetID int) {
	var base wsBaseMsg
	if err := json.Unmarshal(raw, &base); err != nil {
		return
	}

	// Debug: log first few messages of each type
	log.Printf("[%s] MSG topic=%s type=%s", c.Symbol, base.Topic, base.Type)

	switch {
	case contains(base.Topic, "kline"):
		var k klineMsg
		if err := json.Unmarshal(raw, &k); err != nil {
			return
		}
		for _, bar := range k.Data {
			if !bar.Confirm {
				continue
			}
			c.processKline(bar, base.Topic, db, featureSetID)
		}
	case contains(base.Topic, "tickers"):
		c.processTicker(raw)
	case contains(base.Topic, "open_interest"):
		c.processOpenInterest(raw)
	case contains(base.Topic, "liquidation"):
		c.processLiquidation(raw)
	}
}

func (c *BybitClient) processKline(bar klineBar, topic string, db *TimescaleStore, featureSetID int) {
	tf := extractTimeframe(topic)
	op, _ := strconv.ParseFloat(bar.Open, 64)
	hi, _ := strconv.ParseFloat(bar.High, 64)
	lo, _ := strconv.ParseFloat(bar.Low, 64)
	cl, _ := strconv.ParseFloat(bar.Close, 64)
	vol, _ := strconv.ParseFloat(bar.Volume, 64)
	ts, _ := strconv.ParseInt(bar.Start, 10, 64)

	c.mu.Lock()
	store := c.prices[tf]
	c.mu.Unlock()

	store.AddCandle(op, hi, lo, cl, vol)
	e20, e50, e200 := store.EMAs()
	rsi := store.RSI(14)
	atr := store.ATR(14)
	adx := store.ADX(14)
	vema := store.VolumeEMA(20)
	vlt := store.Volatility(14)

	candle := &Candle{
		Time:      time.Unix(ts/1000, 0),
		Symbol:    c.Symbol,
		Timeframe: tf,
		Open:      dec(op), High: dec(hi), Low: dec(lo), Close: dec(cl), Volume: dec(vol),
	}
	if err := db.WriteCandle(candle); err != nil {
		log.Printf("[%s] WriteCandle error: %v", c.Symbol, err)
	}

	fv := &FeatureValues{
		Ts:           candle.Time,
		Symbol:       c.Symbol,
		Timeframe:    tf,
		FeatureSetID: featureSetID,
		Ema20:        dec(e20), Ema50: dec(e50), Ema200: dec(e200),
		Rsi14:        dec(rsi), Atr14: dec(atr), Adx14: dec(adx),
		VolumeEma20:  dec(vema), Volatility14: dec(vlt),
		FundingRate:  c.fundingRate,
		OiDelta1Pct:  c.oiDeltaPct,
		LsRatio:      c.lsRatio,
		LiqLongUSD:   c.liqLong,
		LiqShortUSD:  c.liqShort,
		LiqImbalance: calcLiqImbalance(c.liqLong, c.liqShort),
	}
	if err := db.WriteFeatures(fv); err != nil {
		log.Printf("[%s] WriteFeatures error: %v", c.Symbol, err)
	} else {
		log.Printf("[%s:%s] Candle %s close=%.2f, RSI=%.1f, ATR=%.2f, fund=%.4f%%, OI=%.2f%%",
			c.Symbol, tf, candle.Time.Format("15:04"), cl, rsi, atr, c.fundingRate.InexactFloat64()*100, c.oiDeltaPct.InexactFloat64())
	}
}

func (c *BybitClient) processTicker(raw []byte) {
	var msg struct {
		Data map[string]string `json:"data"`
	}
	if err := json.Unmarshal(raw, &msg); err != nil {
		return
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if v, ok := msg.Data["fundingRate"]; ok {
		c.fundingRate = decStr(v)
	}
}

func (c *BybitClient) processOpenInterest(raw []byte) {
	var msg struct {
		Data struct {
			OpenInterest string `json:"openInterest"`
			Timestamp    string `json:"timestamp"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &msg); err != nil {
		return
	}
	oi := decStr(msg.Data.OpenInterest)
	c.mu.Lock()
	newOI := oi.InexactFloat64()
	oldOI := c.oiDeltaPct.InexactFloat64()
	if oldOI != 0 && oldOI > 0 {
		c.oiDeltaPct = dec((newOI - oldOI) / oldOI * 100)
	} else {
		c.oiDeltaPct = oi
	}
	c.mu.Unlock()
}

func (c *BybitClient) processLiquidation(raw []byte) {
	var msg struct {
		Data struct {
			Side string `json:"side"`
			Size string `json:"size"`
		} `json:"data"`
	}
	if err := json.Unmarshal(raw, &msg); err != nil {
		return
	}
	sz := decStr(msg.Data.Size)
	c.mu.Lock()
	if msg.Data.Side == "Buy" {
		c.liqShort = c.liqShort.Add(sz)
	} else {
		c.liqLong = c.liqLong.Add(sz)
	}
	c.mu.Unlock()
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && (s[:len(substr)] == substr || s[len(s)-len(substr):] == substr))
}

func extractTimeframe(topic string) string {
	parts := split2(topic, ".")
	if len(parts) >= 2 {
		return parts[1]
	}
	return "15m"
}

func split2(s, sep string) []string {
	for i := 0; i < len(s)-len(sep); i++ {
		if s[i:i+len(sep)] == sep {
			return []string{s[:i], s[i+len(sep):]}
		}
	}
	return []string{s}
}

func dec(f float64) decimal.Decimal {
	return decimal.NewFromFloat(math.Round(f*1e8) / 1e8)
}

func decStr(s string) decimal.Decimal {
	d, err := decimal.NewFromString(s)
	if err != nil {
		return decimal.Zero
	}
	return d
}

func calcLiqImbalance(long, short decimal.Decimal) decimal.Decimal {
	if long.Add(short).IsZero() {
		return decimal.Zero
	}
	return short.Sub(long).Div(long.Add(short)).Mul(decimal.NewFromInt(100))
}
