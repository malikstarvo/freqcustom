EDGE_STUDY_SCHEMA = {
    "type": "object",
    "properties": {
        "edge_study": {
            "type": "object",
            "properties": {
                "database_url": {
                    "type": "string",
                    "description": "TimescaleDB connection string (postgresql://user:pass@host:5432/db)",
                },
            },
            "required": ["database_url"],
        },
    },
}


EDGE_STUDY_CLI_OPTIONS = [
    {
        "name": "--symbol",
        "help": "Trading symbol (e.g. BTCUSDT)",
        "type": str,
    },
    {
        "name": "--symbols",
        "help": "Comma-separated trading symbols",
        "type": str,
    },
    {
        "name": "--timeframe",
        "help": "Timeframe for analysis (default: 15m)",
        "type": str,
        "default": "15m",
    },
    {
        "name": "--timeframes",
        "help": "Comma-separated timeframes",
        "type": str,
    },
    {
        "name": "--horizons",
        "help": "Label horizons in bars (default: 4,12,24)",
        "type": str,
        "default": "4,12,24",
    },
    {
        "name": "--feature-set-id",
        "help": "Feature set ID in TimescaleDB (default: 1)",
        "type": int,
        "default": 1,
    },
    {
        "name": "--output",
        "help": "Output directory for reports (default: edge_study_results)",
        "type": str,
        "default": "edge_study_results",
    },
]
