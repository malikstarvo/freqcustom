package main

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/shopspring/decimal"
)

type TimescaleStore struct {
	pool *pgxpool.Pool
	mu   sync.Mutex
}

func NewTimescaleStore(dsn string) (*TimescaleStore, error) {
	cfg, err := pgxpool.ParseConfig(dsn)
	if err != nil {
		return nil, err
	}
	cfg.MaxConns = 10

	pool, err := pgxpool.NewWithConfig(context.Background(), cfg)
	if err != nil {
		return nil, err
	}

	if err := pool.Ping(context.Background()); err != nil {
		pool.Close()
		return nil, err
	}

	fmt.Println("Connected to TimescaleDB")
	return &TimescaleStore{pool: pool}, nil
}

func (s *TimescaleStore) Close() {
	s.pool.Close()
}

type Candle struct {
	Time      time.Time
	Symbol    string
	Timeframe string
	Open      decimal.Decimal
	High      decimal.Decimal
	Low       decimal.Decimal
	Close     decimal.Decimal
	Volume    decimal.Decimal
}

type FeatureValues struct {
	Ts            time.Time
	Symbol        string
	Timeframe     string
	FeatureSetID  int
	Ema20         decimal.Decimal
	Ema50         decimal.Decimal
	Ema200        decimal.Decimal
	Rsi14         decimal.Decimal
	Atr14         decimal.Decimal
	Adx14         decimal.Decimal
	VolumeEma20   decimal.Decimal
	Volatility14  decimal.Decimal
	FundingRate   decimal.Decimal
	OiDelta1Pct   decimal.Decimal
	LsRatio       decimal.Decimal
	LiqLongUSD    decimal.Decimal
	LiqShortUSD   decimal.Decimal
	LiqImbalance  decimal.Decimal
}

func (s *TimescaleStore) WriteCandle(c *Candle) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	_, err := s.pool.Exec(context.Background(),
		`INSERT INTO candles (time, symbol, timeframe, open, high, low, close, volume)
		 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		 ON CONFLICT (time, symbol, timeframe) DO UPDATE SET
		   open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
		   close = EXCLUDED.close, volume = EXCLUDED.volume`,
		c.Time, c.Symbol, c.Timeframe, c.Open, c.High, c.Low, c.Close, c.Volume,
	)
	return err
}

func (s *TimescaleStore) WriteFeatures(fv *FeatureValues) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	_, err := s.pool.Exec(context.Background(),
		`INSERT INTO feature_values
		 (ts, symbol, timeframe, feature_set_id,
		  ema20, ema50, ema200, rsi14, atr14, adx14,
		  volume_ema20, volatility14,
		  funding_rate, oi_delta_1_pct, ls_ratio,
		  liq_long_usd, liq_short_usd, liq_imbalance)
		 VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)`,
		fv.Ts, fv.Symbol, fv.Timeframe, fv.FeatureSetID,
		fv.Ema20, fv.Ema50, fv.Ema200, fv.Rsi14, fv.Atr14, fv.Adx14,
		fv.VolumeEma20, fv.Volatility14,
		fv.FundingRate, fv.OiDelta1Pct, fv.LsRatio,
		fv.LiqLongUSD, fv.LiqShortUSD, fv.LiqImbalance,
	)
	return err
}
