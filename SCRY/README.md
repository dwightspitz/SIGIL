# SCRY - Clean SIGIL Backtester

**Welcome to your fresh, minimal backtesting workspace!**

## What is SCRY?

SCRY is a clean, streamlined version of the SIGIL backtester with ONLY the essential files needed to run backtests. No bloat, no confusion, just what works.

**From 115+ files → 13 essential files (99% reduction!)**

---

## Quick Start

### Launch the GUI
```bash
cd "C:\Users\Randy Buhr\Documents\Personal\SIGIL\SCRY"
python launch_gui.py
```

The GUI will open with:
- ✅ Dropdown date selectors (YYYY, MM, DD)
- ✅ Ticker selection (cached data)
- ✅ LONG/SHORT strategy selection
- ✅ Single backtest or optimization mode
- ✅ Results display and export

---

## What's Included (13 Files)

### Core Engine (6 files)
1. **sigil_backtester.py** - Event-driven backtest engine
2. **sigil_backtester_vectorized.py** - Vectorized version (faster)
3. **sigil_strategy.py** - Donchian Channel signal logic
4. **data_loader.py** - Data fetching (yfinance primary, cache-first)
5. **metrics.py** - 10 DATA HELPER metrics + standard metrics
6. **fast_optimizer.py** - Parallel optimization with FIXED Donchian calc

### Indicators & Utils (3 files)
7. **donchian.py** - Donchian Channel calculations
8. **position_sizing.py** - Turtle position sizing
9. **exporter.py** - DATA HELPER CSV export

### GUI (2 files)
10. **sigil_gui.py** - Main GUI with dropdown date selectors
11. **launch_gui.py** - Simple launcher with error checking

### Config (2 files)
12. **config.py** - Default parameters
13. **requirements.txt** - Python dependencies

### Documentation (3 files - bonus)
- **README.md** - This file
- **GETTING_STARTED.md** - Detailed guide
- **MEMORY_OPTIMIZATION.md** - Optimization tips
- **DATE_PICKER_UPDATE.md** - Date picker changelog

---

## Features

### ✅ What Works
- Single backtest (LONG/SHORT)
- Optimization mode (parameter grid search)
- Cache-first data loading (yfinance)
- DATA HELPER CSV export
- 10 custom performance metrics
- Parallel optimization
- Config persistence
- Dropdown date selectors (no calendar popup)
- **FIXED Donchian calculation** (matches TradingView)

### ❌ What's Removed
- Test files and debug scripts
- Experimental implementations
- Alternative GUIs
- Visualization utilities
- Large result files
- Memory debugging tools

---

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Required Packages
- yfinance (primary data source)
- pandas (data manipulation)
- numpy (calculations)
- scipy (Sharpe/Sortino)
- joblib (parallel optimization)
- openpyxl (Excel export - optional)

**Note**: tkinter is built into Python on Windows/macOS

---

## Usage

### Single Backtest
1. Launch GUI: `python launch_gui.py`
2. Select ticker (e.g., SPY)
3. Set date range with dropdowns
4. Set DC parameters (Top/Bottom Length & Offset)
5. Choose strategy (LONG/SHORT/BOTH)
6. Click "Run Backtest"

### Optimization
1. Launch GUI
2. Check "Enable Optimization"
3. Set parameter ranges (min, max, step)
4. Click "Run Backtest"
5. Results show best parameters

### Export Results
After backtest completes, click "Export to DATA HELPER" to save CSV for analysis.

---

## Data

### Cache Location
`data/cache/` - Auto-created on first run

### Supported Data Sources
- **yfinance** (primary) - Free, unlimited
- **databento** (optional) - Professional data, requires API key

### Cache Format
Files are cached as: `{TICKER}_{START}_{END}_{TIMEFRAME}.csv`

Example: `SPY_2024-01-01_2024-12-31_1d.csv`

---

## Configuration

### Default Parameters
See [config.py](config.py) for defaults:
- Initial Capital: $100,000
- Top DC Length: 110
- Top DC Offset: 65
- Bottom DC Length: 90
- Bottom DC Offset: 55

### Last Used Settings
Saved to `sigil_config.json` - Auto-loads on GUI restart

---

## Performance

### Optimization Speed
- **Small grids** (10-50 combos): ~5-30 seconds
- **Medium grids** (100-500 combos): ~1-5 minutes
- **Large grids** (1000+ combos): ~10-30 minutes

Speed depends on:
- Data timeframe (daily vs 30-minute)
- Date range (longer = more data)
- Number of parameter combinations
- CPU cores (parallel processing)

---

## Troubleshooting

### GUI Won't Launch
1. Check Python version: `python --version` (need 3.9+)
2. Install dependencies: `pip install -r requirements.txt`
3. Check tkinter: `python -c "import tkinter"`

### No Data Found
1. Check internet connection (yfinance needs internet)
2. Try "Refresh Cache" button in GUI
3. Verify ticker symbol is valid

### Backtest Taking Too Long
- Use daily data instead of 30-minute
- Reduce date range
- Use cached data (check `data/cache/`)

### Results Don't Match TradingView
- Verify same date range
- Check DC parameter values match
- Ensure using same strategy (LONG vs SHORT)
- **Note**: Donchian calculation was FIXED - older results may differ

---

## File Structure

```
SCRY/
├── Core Engine
│   ├── sigil_backtester.py
│   ├── sigil_backtester_vectorized.py
│   ├── sigil_strategy.py
│   ├── data_loader.py
│   ├── metrics.py
│   └── fast_optimizer.py
│
├── Indicators/Utils
│   ├── donchian.py
│   ├── position_sizing.py
│   └── exporter.py
│
├── GUI
│   ├── sigil_gui.py
│   └── launch_gui.py
│
├── Config
│   ├── config.py
│   ├── requirements.txt
│   └── sigil_config.json (auto-created)
│
├── Documentation
│   ├── README.md (this file)
│   ├── GETTING_STARTED.md
│   ├── MEMORY_OPTIMIZATION.md
│   └── DATE_PICKER_UPDATE.md
│
└── Data (auto-created)
    ├── cache/
    └── checkpoints/
```

---

## What's Different from BACKTESTER?

| Aspect | BACKTESTER | SCRY |
|--------|-----------|------|
| Total Files | 115+ | 13 |
| Size | ~50+ MB | ~270 KB |
| Test Files | 15+ | 0 |
| Experimental Code | 6-8 files | 0 |
| Date Picker | Calendar popup | Dropdown menus |
| Donchian Calc | Had bug | **FIXED** |
| Memory Usage | High | Optimized |

---

## Recent Updates

### 2025-12-27
- ✅ Created SCRY clean directory
- ✅ Replaced calendar with dropdown date selectors
- ✅ Fixed Donchian channel calculation (now matches TradingView)
- ✅ Optimized memory usage in fast_optimizer
- ✅ Removed all bloat (test files, experimental code)

---

## Support

For issues or questions:
1. Check [GETTING_STARTED.md](GETTING_STARTED.md)
2. Review [MEMORY_OPTIMIZATION.md](MEMORY_OPTIMIZATION.md)
3. Verify all dependencies installed
4. Check data cache exists

---

## Next Steps

1. **First Run**: Launch GUI and verify it works
2. **Download Data**: Use "Tools → Download Data" to cache SPY
3. **Test Backtest**: Run a simple backtest (default parameters)
4. **Try Optimization**: Small grid (5-10 combinations)
5. **Export**: Send results to DATA HELPER for analysis

---

**Enjoy your clean, fast, functional backtester! 🚀**

---

*Created: 2025-12-27*
*Location: `C:\Users\Randy Buhr\Documents\Personal\SIGIL\SCRY`*
*From: BACKTESTER (cleaned and streamlined)*
