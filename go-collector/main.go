package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"
)

type Config struct {
	TimescaleDSN string
	Symbols      []string
	Timeframes   []string
	FeatureSetID int
}

func LoadConfig() *Config {
	return &Config{
		TimescaleDSN: getEnv("TIMESCALE_DSN", "postgresql://freqtrade:freqtrade@localhost:5432/freqtrade?sslmode=disable"),
		Symbols:      splitEnv("BYBIT_SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT"),
		Timeframes:   splitEnv("BYBIT_TIMEFRAMES", "15m,1h,4h"),
		FeatureSetID: getEnvInt("FEATURE_SET_ID", 1),
	}
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		if i, err := strconv.Atoi(v); err == nil {
			return i
		}
	}
	return fallback
}

func splitEnv(key, fallback string) []string {
	raw := getEnv(key, fallback)
	parts := strings.Split(raw, ",")
	var result []string
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			result = append(result, p)
		}
	}
	return result
}

func main() {
	cfg := LoadConfig()
	fmt.Printf("Go Collector starting: %d symbols, %d timeframes\n", len(cfg.Symbols), len(cfg.Timeframes))
	fmt.Printf("TimescaleDB: %s\n", maskDSN(cfg.TimescaleDSN))

	db, err := NewTimescaleStore(cfg.TimescaleDSN)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to connect to TimescaleDB: %v\n", err)
		os.Exit(1)
	}
	defer db.Close()

	for _, symbol := range cfg.Symbols {
		client := NewBybitClient(symbol, cfg.Timeframes)
		go client.Stream(db, cfg.FeatureSetID)
	}

	select {}
}

func maskDSN(dsn string) string {
	if idx := strings.Index(dsn, "@"); idx > 0 {
		return "***" + dsn[idx:]
	}
	return dsn
}
