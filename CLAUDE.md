# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## SIGIL Project Context

**SIGIL** = Strategic Intelligence Gathering and Investment Logic
**Project Lead**: Randy Buhr
**Focus**: Quantitative Trading Systems & Risk Management

This repository is part of the broader SIGIL trading analysis workspace, which includes:
- **SIGILTASK**: Task management and calendar generation (this repo)
- **PINESCRIPT**: TradingView Pine Script strategies (HFM, TRAMA_Turtle)
- **DATA HELPER**: TradingView backtest CSV processor and analyzer
- **STRATEGIES/BACKTESTING/RISK_MANAGEMENT**: [Planned] Advanced trading infrastructure

## Project Overview

This is a Python-based Exchange Task Creator application built with Tkinter GUI. The application manages tasks and generates both task files (.ics) and calendar events (.ics) with Microsoft Exchange compatibility.

## Core Architecture

- **Main Application**: `exchange_task_creator_v1_80_13.py` - Latest version of the task creator GUI
- **Legacy Versions**: `aTask1.py`, `aTask1.80.py`, `aTask1.80.12.py`, `aTask1.81.py` - Previous iterations
- **Data Storage**: JSON files for configuration and task data
  - `tasks.json` - Task data storage
  - `categories.json` - Task categories 
  - `projects.json` - Project definitions
  - `contacts.json` - Contact information
  - `locations.json` - Saved locations
- **Output Directories**:
  - `Tasks/` - Generated .ics task files
  - `Events/` - Generated .ics calendar event files

## Running the Application

```bash
python exchange_task_creator_v1_80_13.py
```

Or any of the legacy versions:
```bash
python aTask1.py
python aTask1.81.py
```

## Key Features

- **Task Management**: Create, edit, and track tasks with full metadata (priority, status, dates, categories, etc.)
- **iCalendar Export**: Generates .ics files compatible with Microsoft Exchange and EM Client
- **Dual Output**: Creates both task files (VTODO) and calendar events (VEVENT) for each task
- **Import/Export**: Supports importing from .ics, .json, .txt, and .csv files
- **Contact Integration**: Manages contact database for task assignment
- **Project Organization**: Groups tasks by projects and categories

## Data Structure

Tasks contain these key fields:
- `id`, `subject`, `project`, `priority`, `status`, `progress`
- Date fields: `start_date`, `due_date`, `reminder_date`
- Metadata: `category`, `owner`, `location`, `description`
- Generated: `created_date`

## Dependencies

The application uses standard Python libraries:
- `tkinter` - GUI framework
- `datetime` - Date/time handling
- `json` - Data persistence
- `os`, `uuid`, `calendar` - Utilities
- Optional: `tkinterdnd2` - Drag and drop support (gracefully degrades if unavailable)

---

## Pine Script Trading Strategies

Located in: `C:\Users\Randy Buhr\Documents\Personal\SIGIL\PINESCRIPT\`

### HFM.pine - ATR Hedge Fund Manager [SIGIL]

**Strategy Type**: ATR-based Renko momentum with Turtle position sizing

#### Core Features:
- **Simulated Renko Bars**: Uses ATR to calculate dynamic box size, avoiding request.security() repainting issues
- **Turtle Position Sizing**: 20-day ATR-based position sizing for consistent risk management
- **Position Scale Factor**: Global multiplier to scale position sizes across multiple strategies
- **Pyramiding**: Supports multiple entries with add-on positions
- **Hedge Logic**: Partial position exit on reversal signals

#### Key Parameters:
- **ATR Multiplier for Box Size**: Controls Renko brick size
  - Test Range: 16.4 ± 1.7, Step: 0.1 (14.7 to 18.1) = 35 values
- **ATR Length**: Period for Renko ATR calculation
  - Test Range: 550 ± 70, Step: 1 (480 to 620) = 141 values
  - **Total Optimization Combinations**: ~4,935 backtests
- **Position Scale**: Multiplier for position sizing (default: 1.0)
  - Use <1 to scale down when running multiple strategies
  - Use >1 to scale up for more aggressive sizing

#### Strategy Logic:
1. **Entry**: New up brick after down brick (reversal)
2. **Add**: Consecutive up brick (trend continuation)
3. **Hedge**: New down brick after up brick (66% exit)
4. **Exit**: Consecutive down brick (full exit except hodl%)

#### Position Sizing Formula:
```
atr = ta.sma(true_range_daily, 20)
n_atr = (atr / close_daily)  // Turtle method
poe = n_atr * 100 * position_scale
poe_add = (n_atr/2) * 100 * position_scale
```

#### Visualization:
- Renko close/open levels plotted
- Up/down targets showing next brick formation levels
- Green/red zones between current price and targets
- Signal markers for entry/exit/hedge points

### TRAMA_Turtle.pine

**Strategy Type**: TRAMA/THMA cloud crossover with ATR pyramiding

#### Core Features:
- **Triple Hull Moving Average (THMA)**: Advanced smoothing for trend detection
- **TRAMA (Triangular Adaptive Moving Average)**: Volatility-adaptive trend following
- **Dual TRAMA Support**: Two independent TRAMA clouds with separate timeframes
- **Multi-Timeframe**: Each indicator can use different timeframes
- **ATR Pyramiding**: Add to positions every 0.5 ATR move

#### Key Parameters:
- **THMA Length**: 50 (configurable timeframe)
- **TRAMA Length**: 20 (configurable timeframe)
- **TRAMA 2 Length**: 50 (configurable timeframe)
- **ATR Length**: 3920 bars for position sizing
- **ATR Add Multiple**: 0.5 (add every 0.5 ATR move)

#### Strategy Logic:
- **Entry**: Price crosses above ANY THMA/TRAMA line
- **Add**: Price moves 0.5 ATR from last add price
- **Exit**: Price crosses below ANY THMA/TRAMA line

---

## Python Backtesting Development Plan

### Goal: Build Python Backtester for HFM Strategy

**Status**: Planned for future development (conversation saved 2025-01)

#### Why Python Instead of TradingView:
1. **Free Data Sources**: Can use yfinance, Alpha Vantage, Polygon.io
2. **Better Optimization**: Can run ~4,935 backtest combinations efficiently
3. **No Rate Limits**: Unlimited local backtesting
4. **Custom Analysis**: Full control over metrics and reporting
5. **Integration**: Can connect to SIGIL DATA HELPER for analysis

#### Recommended Tech Stack:

**Data Sources (Free)**:
- `yfinance` - Yahoo Finance API (daily data, unlimited)
- `Alpha Vantage` - Intraday data (500 calls/day free tier)
- `Polygon.io` - Limited free tier
- `CCXT` - Free crypto data for testing

**Backtesting Libraries**:
- `backtrader` - Most popular, mature ecosystem
- `vectorbt` - Fast vectorized backtesting, great for optimization
- `backtesting.py` - Simple, clean API

**Analysis**:
- `pandas` - Data manipulation
- `numpy` - Numerical calculations
- `matplotlib`/`plotly` - Visualization
- Integration with existing DATA HELPER for TradingView comparison

#### Implementation Checklist:
- [ ] Set up Python environment with required libraries
- [ ] Implement ATR-based Renko simulation logic
- [ ] Implement Turtle position sizing (20-day ATR)
- [ ] Build entry/exit signal generation
- [ ] Create parameter optimization framework (4,935 combinations)
- [ ] Generate performance reports and metrics
- [ ] Export results to DATA HELPER format for analysis
- [ ] Compare Python backtest vs TradingView results

#### Strategy Components to Implement:

**1. Renko Simulation**:
```python
# Simulated Renko brick calculation
# - Track renko_close, renko_open, renko_direction
# - Calculate box_size from ATR * multiplier
# - Form bricks when price moves >= box_size
# - Support multiple bricks per bar
```

**2. Signal Generation**:
```python
# Entry: New up brick after down brick
# Add: Consecutive up brick
# Hedge: New down brick after up brick (66% exit)
# Exit: Consecutive down brick (exit except hodl%)
```

**3. Position Sizing**:
```python
# Turtle method: atr / close
# POE = n_atr * 100 * position_scale
# POE_add = (n_atr/2) * 100 * position_scale
```

**4. Optimization Parameters**:
- ATR Multiplier: 14.7 to 18.1 (step 0.1) = 35 values
- ATR Length: 480 to 620 (step 1) = 141 values
- Total: 4,935 backtests

#### Data Requirements:
- **Symbol**: SPY (or SPYU for live trading)
- **Timeframe**: Daily recommended (matches 20-day ATR)
- **Date Range**: 2024-03-01 to 2025-10-12 (or longer)
- **Columns Needed**: Open, High, Low, Close, Volume

#### Expected Outputs:
- Net profit, CAGR, Sharpe ratio, Sortino ratio
- Max drawdown, max run-up
- Win rate, profit factor, avg win/loss
- Risk-adjusted CAGR (DATA HELPER formula)
- Calmar ratio
- Trade-by-trade log with signals
- Equity curve visualization
- Parameter heatmaps for optimization results

#### Integration with SIGIL Ecosystem:
- Export backtest results in DATA HELPER CSV format
- Use DATA HELPER's 10 custom metrics for analysis
- Compare Python results vs TradingView backtests
- Validate strategy logic consistency across platforms

---

## SIGIL DATA HELPER Integration

The TradingView Data Helper (located in `C:\Users\Randy Buhr\Documents\Personal\SIGIL\DATA HELPER\`) provides:

### 10 Automated Performance Metrics:
1. **Risk-Adjusted CAGR**: Custom ERP-based formula with trade frequency
2. **Calmar Ratio**: CAGR / Max Drawdown
3. **Win/Loss Spread**: Avg Win % - Avg Loss %
4. **Trades Per Day**: Trade frequency metric
5. **Equity Curve Smoothness**: Max Run-up / Max Drawdown
6. **Hedge Quality Index**: Loss management effectiveness
7. **Loss Control Metric**: Avg Loss % / Avg Win %
8. **Tail Risk**: Largest Loss % / Avg Loss %
9. **Trade Duration Efficiency**: Net Profit % / Avg Bars in Trades
10. **Market Outperformance (Alpha)**: Net Profit % / Buy & Hold Return %

### Workflow Integration:
1. Export backtest results from TradingView (or Python backtester)
2. Drag-and-drop CSV files into DATA HELPER
3. Automatic calculation of all 10 metrics
4. Interactive visualization with custom chart builder
5. Excel export for advanced analysis

### Use Cases:
- Compare HFM strategy results across different parameters
- Analyze TRAMA_Turtle performance vs other strategies
- Validate Python backtester against TradingView results
- Generate reports for strategy evaluation

---

## File Locations Reference

```
SIGIL/
├── SIGILTASK/task_generator/           # This repo
│   ├── exchange_task_creator_v1_80_13.py
│   ├── tasks.json
│   └── CLAUDE.md                        # This file
├── PINESCRIPT/                          # Trading strategies
│   ├── HFM.pine                         # ATR Hedge Fund Manager
│   └── TRAMA_Turtle.pine                # TRAMA/THMA cloud strategy
├── DATA HELPER/                         # Backtest analysis tool
│   ├── helper.py                        # TradingView CSV processor
│   └── requirements.txt
└── README.md                            # Project overview
```