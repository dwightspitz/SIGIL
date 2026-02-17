"""
SCRY Optimization Analysis Dashboard
Interactive visualization and filtering for consolidated backtest results
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def calculate_derived_metrics(df):
    """
    Calculate derived metrics not present in TradingView CSV export.

    Adds the following columns:
    - Win_Loss_Ratio: Avg_Winning_Trade_Pct / abs(Avg_Losing_Trade_Pct)
    - Avg_RunUp_DD_Ratio: Max_Run_Up_Pct / Avg_Drawdown_Pct

    Parameters:
        df (pd.DataFrame): Input dataframe from CSV

    Returns:
        pd.DataFrame: Dataframe with additional calculated columns
    """
    df_calc = df.copy()

    # Win/Loss Ratio - Primary metric
    if 'Avg_Winning_Trade_Pct' in df_calc.columns and 'Avg_Losing_Trade_Pct' in df_calc.columns:
        df_calc['Win_Loss_Ratio'] = df_calc['Avg_Winning_Trade_Pct'] / abs(df_calc['Avg_Losing_Trade_Pct'])
        df_calc['Win_Loss_Ratio'] = df_calc['Win_Loss_Ratio'].replace([np.inf, -np.inf], np.nan)

    # Avg Run-Up to Drawdown Ratio
    if 'Max_Run_Up_Pct' in df_calc.columns and 'Avg_Drawdown_Pct' in df_calc.columns:
        df_calc['Avg_RunUp_DD_Ratio'] = df_calc['Max_Run_Up_Pct'] / abs(df_calc['Avg_Drawdown_Pct'])
        df_calc['Avg_RunUp_DD_Ratio'] = df_calc['Avg_RunUp_DD_Ratio'].replace([np.inf, -np.inf], np.nan)

    # Win/Loss Spread - Expectancy spread
    if 'Avg_Winning_Trade_Pct' in df_calc.columns and 'Avg_Losing_Trade_Pct' in df_calc.columns:
        df_calc['Win_Loss_Spread'] = df_calc['Avg_Winning_Trade_Pct'] - abs(df_calc['Avg_Losing_Trade_Pct'])

    # Equity Curve Smoothness - Max Run-up / Max Drawdown
    if 'Max_Run_Up_Pct' in df_calc.columns and 'Max_Drawdown_Pct' in df_calc.columns:
        df_calc['Equity_Curve_Smoothness'] = df_calc['Max_Run_Up_Pct'] / abs(df_calc['Max_Drawdown_Pct'])
        df_calc['Equity_Curve_Smoothness'] = df_calc['Equity_Curve_Smoothness'].replace([np.inf, -np.inf], np.nan)

    # Hedge Quality Index - (1 - Loss/Win) × 100
    if 'Avg_Winning_Trade_Pct' in df_calc.columns and 'Avg_Losing_Trade_Pct' in df_calc.columns:
        loss_win_ratio = abs(df_calc['Avg_Losing_Trade_Pct']) / df_calc['Avg_Winning_Trade_Pct']
        df_calc['Hedge_Quality_Index'] = (1 - loss_win_ratio) * 100
        df_calc['Hedge_Quality_Index'] = df_calc['Hedge_Quality_Index'].replace([np.inf, -np.inf], np.nan)

    # Loss Control Metric - Avg Loss % / Avg Win %
    if 'Avg_Winning_Trade_Pct' in df_calc.columns and 'Avg_Losing_Trade_Pct' in df_calc.columns:
        df_calc['Loss_Control_Metric'] = abs(df_calc['Avg_Losing_Trade_Pct']) / df_calc['Avg_Winning_Trade_Pct']
        df_calc['Loss_Control_Metric'] = df_calc['Loss_Control_Metric'].replace([np.inf, -np.inf], np.nan)

    # Tail Risk - Largest Loss % / Avg Loss %
    if 'Largest_Losing_Trade_Pct' in df_calc.columns and 'Avg_Losing_Trade_Pct' in df_calc.columns:
        df_calc['Tail_Risk'] = abs(df_calc['Largest_Losing_Trade_Pct']) / abs(df_calc['Avg_Losing_Trade_Pct'])
        df_calc['Tail_Risk'] = df_calc['Tail_Risk'].replace([np.inf, -np.inf], np.nan)

    # Trade Duration Efficiency - Net Profit % / Avg Bars in Trades
    if 'Net_Profit_Pct' in df_calc.columns and 'Avg_Bars_In_Trades' in df_calc.columns:
        df_calc['Trade_Duration_Efficiency'] = df_calc['Net_Profit_Pct'] / df_calc['Avg_Bars_In_Trades']
        df_calc['Trade_Duration_Efficiency'] = df_calc['Trade_Duration_Efficiency'].replace([np.inf, -np.inf], np.nan)

    # Win/Loss Duration Spread - (Avg Win % / Avg Bars Wins) - (|Avg Loss %| / Avg Bars Losses)
    if all(col in df_calc.columns for col in ['Avg_Winning_Trade_Pct', 'Avg_Bars_In_Winning_Trades',
                                                'Avg_Losing_Trade_Pct', 'Avg_Bars_In_Losing_Trades']):
        win_efficiency = df_calc['Avg_Winning_Trade_Pct'] / df_calc['Avg_Bars_In_Winning_Trades']
        loss_efficiency = abs(df_calc['Avg_Losing_Trade_Pct']) / df_calc['Avg_Bars_In_Losing_Trades']
        df_calc['Win_Loss_Duration_Spread'] = win_efficiency - loss_efficiency
        df_calc['Win_Loss_Duration_Spread'] = df_calc['Win_Loss_Duration_Spread'].replace([np.inf, -np.inf], np.nan)

    # Capital Efficiency Metrics
    # Default initial capital to 100000 if not specified
    initial_capital = 100000  # TODO: Make this configurable via sidebar

    if 'Account_Size_Required' in df_calc.columns:
        # Capital Leverage Ratio = Account Size Required / Initial Capital
        df_calc['Capital_Leverage_Ratio'] = df_calc['Account_Size_Required'] / initial_capital
        df_calc['Capital_Leverage_Ratio'] = df_calc['Capital_Leverage_Ratio'].replace([np.inf, -np.inf], np.nan)

        # Capital Efficiency Ratio = Return on Account Size Required / Capital Leverage Ratio
        if 'Return_On_Account_Size_Required' in df_calc.columns:
            df_calc['Capital_Efficiency_Ratio'] = (
                df_calc['Return_On_Account_Size_Required'] / df_calc['Capital_Leverage_Ratio']
            )
            df_calc['Capital_Efficiency_Ratio'] = df_calc['Capital_Efficiency_Ratio'].replace([np.inf, -np.inf], np.nan)

    return df_calc


def detect_strategy_type(df):
    """
    Detect strategy type for each row (DC_ONLY, FULL_SIGIL, or PARTIAL).

    DC_ONLY strategies only use Donchian Channels (DC_Length, DC_Offset).
    FULL_SIGIL strategies use all parameters including TRAMA, ATR, HHV.

    Parameters:
        df (pd.DataFrame): Input dataframe

    Returns:
        pd.DataFrame: Dataframe with added 'Strategy_Type' column
    """
    df_type = df.copy()

    # Parameters that are optional (only used in FULL_SIGIL)
    optional_params = ['ATR_Period', 'HHV_Period', 'ATR_Multiplier', 'TRAMA_Length', 'TRAMA_Lookback']

    def classify_row(row):
        # Count how many optional parameters are filled
        filled_count = 0
        total_optional = 0

        for param in optional_params:
            if param in row:
                total_optional += 1
                val = row[param]
                # Check if parameter is filled (not null, not empty string, not 0)
                if pd.notna(val) and val != '' and val != 0:
                    filled_count += 1

        if total_optional == 0:
            return 'UNKNOWN'  # No optional columns present
        elif filled_count == 0:
            return 'DC_ONLY'
        elif filled_count == total_optional:
            return 'FULL_SIGIL'
        else:
            return 'PARTIAL'

    df_type['Strategy_Type'] = df_type.apply(classify_row, axis=1)

    return df_type


def get_relevant_params_for_strategy(strategy_type):
    """
    Get list of relevant parameter columns based on strategy type.

    Parameters:
        strategy_type (str): 'DC_ONLY', 'FULL_SIGIL', or 'PARTIAL'

    Returns:
        list: List of parameter column names to display
    """
    # Base parameters (always shown) - handle both legacy and new format
    base_params = ['Ticker', 'Strategy']

    # Add DC parameters based on what's available in the dataframe
    dc_params = ['Top_DC_Length', 'Top_DC_Offset', 'Bottom_DC_Length', 'Bottom_DC_Offset',
                 'Top_Channel_Enabled', 'Bottom_Channel_Enabled']

    # Legacy format support
    legacy_dc_params = ['DC_Length', 'DC_Offset']

    # Optional parameters (only for FULL_SIGIL)
    optional_params = ['ATR_Period', 'HHV_Period', 'ATR_Multiplier', 'TRAMA_Length', 'TRAMA_Lookback']

    if strategy_type == 'DC_ONLY':
        return base_params + dc_params + legacy_dc_params
    elif strategy_type == 'FULL_SIGIL':
        return base_params + dc_params + legacy_dc_params + optional_params
    else:  # PARTIAL or UNKNOWN
        return base_params + dc_params + legacy_dc_params + optional_params  # Show all for mixed cases


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

# Page config
st.set_page_config(
    page_title="SCRY Analysis Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("SCRY Optimization Analysis Dashboard")
st.markdown("---")

# Sidebar - File Upload
with st.sidebar:
    st.header("Data Import")
    uploaded_file = st.file_uploader(
        "Upload Consolidated CSV",
        type=["csv"],
        help="Load consolidated optimization results"
    )

    st.markdown("---")
    st.markdown("### SIGIL Quantitative")
    st.markdown("**Progressive Testing Analysis**")

# Main content
if uploaded_file is None:
    st.info("Upload a consolidated CSV file to begin analysis")
    st.stop()

# Load data
@st.cache_data
def load_data(file):
    """Load and cache the CSV data"""
    df = pd.read_csv(file)

    # Standardize column names from TradingView export to match dashboard expectations
    # Only map the ": All" aggregate metrics to avoid duplicates
    # Leave Long/Short versions untouched
    column_mapping = {
        # Performance Metrics - Only map ": All" versions
        'Net P&L %: All': 'Net_Profit_Pct',
        'Total trades: All': 'Total_Trades',
        'Percent profitable: All': 'Percent_Profitable',
        'Profit factor: All': 'Profit_Factor',

        # Drawdown Metrics - Map close-to-close versions
        'Max equity drawdown (close-to-close) %': 'Max_Drawdown_Pct',
        'Avg equity drawdown (close-to-close) %': 'Avg_Drawdown_Pct',

        # Run-up Metrics
        'Max equity run-up (close-to-close) %': 'Max_Run_Up_Pct',

        # Trade Metrics - Only map ": All" versions
        'Avg P&L %: All': 'Avg_Trade_Pct',
        'Avg # bars in trades: All': 'Avg_Bars_In_Trades',

        # Winning Trade Metrics - Only map ": All" versions
        'Avg winning trade %: All': 'Avg_Winning_Trade_Pct',
        'Avg # bars in winning trades: All': 'Avg_Bars_In_Winning_Trades',

        # Losing Trade Metrics - Only map ": All" versions
        'Avg losing trade %: All': 'Avg_Losing_Trade_Pct',
        'Avg # bars in losing trades: All': 'Avg_Bars_In_Losing_Trades',

        # Extreme Trade Metrics - Only map ": All" versions
        'Largest winning trade percent: All': 'Largest_Winning_Trade_Pct',
        'Largest losing trade percent: All': 'Largest_Losing_Trade_Pct',

        # Benchmark
        'Buy & hold % gain': 'Buy_And_Hold_Return_Pct',

        # Capital Efficiency Metrics
        'Account size required': 'Account_Size_Required',
        'Return on account size required: All': 'Return_On_Account_Size_Required',

        # Parameter columns (from TradingView strategy properties panel)
        '__Donchian Length': 'Top_DC_Length',
        '__Donchian Offset': 'Top_DC_Offset',
        '__ATR Period': 'ATR_Period',
        '__HHV Period': 'HHV_Period',
        '__Multiplier': 'ATR_Multiplier',
        '__TRAMA Length': 'TRAMA_Length',
        '__Slope Lookback': 'TRAMA_Lookback',

        # MACD Slope parameters
        '__Use MACD Slope': '__Use_MACD_Slope',
        '__Source': '__Source',
        '__Fast Length': '__Fast_Length',
        '__Slow Length': '__Slow_Length',
        '__Signal Length': '__Signal_Length',
        '__Histogram Smoothing (SMA)': '__Histogram_Smoothing_SMA',
        '__Slope Lookback (bars)': '__Slope_Lookback_bars',
        '__Entry Slope Threshold (°)': '__Entry_Slope_Threshold',
        '__Exit Slope Threshold (°)': '__Exit_Slope_Threshold',

        # RSI Slope parameters
        '__Use RSI Slope': '__Use_RSI_Slope',
        '__RSI Length': '__RSI_Length',
        '__Smoothing Type': '__Smoothing_Type',
        '__Smoothing Length': '__Smoothing_Length',

        # Hold % parameters
        '__Donchian Channel Hold %': '__Donchian_Channel_Hold_Pct',
        '__MACD Slope Hold %': '__MACD_Slope_Hold_Pct',
        '__RSI Slope Hold %': '__RSI_Slope_Hold_Pct',
        '__Trailing Stop Hold %': '__Trailing_Stop_Hold_Pct',

        # Other toggle parameters
        '__Use Donchian Channel': '__Use_Donchian_Channel',
        '__Use Trailing Stop for Exit': '__Use_Trailing_Stop',
        '__Use TRAMA Slope Filter': '__Use_TRAMA_Slope_Filter',
        '__Enable ATR Position Sizing': '__Enable_ATR_Position_Sizing',
        '__Position Scale Factor': '__Position_Scale_Factor',
    }

    # Rename columns that exist in the dataframe
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Remove duplicate columns (keep first occurrence)
    # This handles cases where TradingView exports both base columns and ": All" versions
    df = df.loc[:, ~df.columns.duplicated(keep='first')]

    # Calculate derived metrics
    df = calculate_derived_metrics(df)

    # Detect strategy types
    df = detect_strategy_type(df)

    return df

try:
    df = load_data(uploaded_file)

    # Display data info with date range
    info_col1, info_col2, info_col3 = st.columns(3)

    with info_col1:
        st.success(f"**{len(df):,}** optimization results loaded")

    with info_col2:
        # Extract date range from data
        if 'Start_Date' in df.columns and 'End_Date' in df.columns:
            start_date = df['Start_Date'].iloc[0] if not df.empty else "N/A"
            end_date = df['End_Date'].iloc[0] if not df.empty else "N/A"
            st.info(f"**Date Range:** {start_date} to {end_date}")
        elif 'Date_Range' in df.columns:
            date_range = df['Date_Range'].iloc[0] if not df.empty else "N/A"
            st.info(f"**Date Range:** {date_range}")
        else:
            st.info("**Date Range:** Not available in CSV")

    with info_col3:
        # Show unique tickers
        if 'Ticker' in df.columns:
            tickers = df['Ticker'].unique()
            ticker_str = ", ".join(tickers) if len(tickers) <= 3 else f"{len(tickers)} tickers"
            st.info(f"**Tickers:** {ticker_str}")

    # Strategy Type Distribution
    if 'Strategy_Type' in df.columns:
        st.markdown("---")
        type_col1, type_col2, type_col3, type_col4 = st.columns(4)

        type_counts = df['Strategy_Type'].value_counts()

        with type_col1:
            dc_only = type_counts.get('DC_ONLY', 0)
            st.metric("DC_ONLY Strategies", f"{dc_only:,}")

        with type_col2:
            full_sigil = type_counts.get('FULL_SIGIL', 0)
            st.metric("FULL_SIGIL Strategies", f"{full_sigil:,}")

        with type_col3:
            partial = type_counts.get('PARTIAL', 0)
            st.metric("PARTIAL Strategies", f"{partial:,}")

        with type_col4:
            # Show dominant strategy type
            dominant = type_counts.idxmax() if len(type_counts) > 0 else 'N/A'
            st.metric("Dominant Type", dominant)

except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# Data preview
with st.expander("Data Preview", expanded=False):
    st.dataframe(df.head(10), use_container_width=True)
    st.caption(f"Showing first 10 of {len(df):,} rows")

# Metric Glossary
with st.expander("📊 Metric Glossary", expanded=False):
    st.markdown("### Filter Metrics Guide")
    st.caption("⚠️ Note: Some metrics (CAGR, Risk-Adjusted CAGR, Calmar Ratio) require data not available in current CSV export and have been removed from filters.")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("""
        **Win/Loss Analysis**

        **Win/Loss Ratio** ⭐ PRIMARY
        - Formula: `Avg Win % / |Avg Loss %|`
        - Good: > 2.0 | Best: > 3.0
        - Interpretation: How many times larger wins are vs losses

        **Profit Factor**
        - Formula: `Gross Profit / Gross Loss`
        - Good: > 1.5 | Best: > 2.0
        - Interpretation: Dollars won per dollar lost

        **Win/Loss Spread**
        - Formula: `Avg Win % - Avg Loss %`
        - Good: Higher is better
        - Interpretation: Raw expectancy difference

        **Loss Control Metric** (Bottom filter)
        - Formula: `Avg Loss % / Avg Win %`
        - Good: < 0.5 | Best: < 0.3
        - Interpretation: Loss size relative to wins

        ---

        **Risk Management**

        **Max Drawdown %** (Bottom filter)
        - Definition: Maximum peak-to-trough decline
        - Good: Lower is better
        - Interpretation: Worst-case capital preservation

        **Avg Drawdown %** (Bottom filter)
        - Definition: Average close-to-close drawdown
        - Good: Lower is better
        - Interpretation: Typical drawdown magnitude

        **Tail Risk** (Bottom filter)
        - Formula: `Largest Loss % / Avg Loss %`
        - Good: < 2.0 | Best: < 1.5
        - Interpretation: Extreme loss outlier detection

        **Avg Run-Up/DD Ratio** ⭐ NEW
        - Formula: `Max Run-up % / Avg Drawdown %`
        - Good: > 15 | Best: > 20
        - Interpretation: Upside potential vs typical drawdown
        """)

    with col_g2:
        st.markdown("""
        **Efficiency & Consistency**

        **Equity Curve Smoothness**
        - Formula: `Max Run-up % / Max Drawdown %`
        - Good: > 3.0 | Best: > 5.0
        - Interpretation: Consistency of equity curve growth

        **Trade Duration Efficiency**
        - Formula: `Net Profit % / Avg Bars in Trades`
        - Good: Higher is better
        - Interpretation: Profit per time unit held

        **Win/Loss Duration Spread**
        - Formula: `(Avg Win % / Avg Bars Wins) - (|Avg Loss %| / Avg Bars Losses)`
        - Good: Positive values
        - Interpretation: Making money faster than losing it

        **Hedge Quality Index**
        - Formula: `(1 - Loss/Win Ratio) × 100`
        - Good: Higher is better (0-100 scale)
        - Interpretation: Loss management effectiveness

        ---

        **Overall Performance**

        **Net Profit %**
        - Definition: Total return over backtest period
        - Good: Higher is better
        - Interpretation: Absolute performance

        **Win Rate %** (Percent Profitable)
        - Definition: Percentage of winning trades
        - Good: Higher is better
        - Note: Quality matters more than quantity

        **Max Run-Up %**
        - Definition: Maximum peak-to-bottom gain
        - Good: Higher is better
        - Interpretation: Profit potential strength

        ---

        **Strategy Types**
        - **DC_ONLY**: Uses only Donchian Channels (DC_Length, DC_Offset)
        - **FULL_SIGIL**: Uses all parameters (DC + ATR + HHV + TRAMA)
        - **PARTIAL**: Uses some but not all optional parameters
        """)

    st.markdown("---")
    st.caption("💡 For detailed formulas and methodology, see CLAUDE.md in the SIGIL repository")

st.markdown("---")

# Analysis Selection
st.header("Chart Presets")

def get_chart_preset_config(preset_name):
    """
    Get chart configuration for preset analysis types.

    Returns dict with: x_axis, y_axis, size_metric, color_metric, title, reverse_x
    """
    presets = {
        "Win/Loss Analysis": {
            'x_axis': 'Avg_Drawdown_Pct',
            'y_axis': 'Win_Loss_Ratio',
            'size_metric': 'Total_Trades',
            'color_metric': 'Profit_Factor',
            'title': 'Win/Loss Ratio vs Avg Drawdown',
            'reverse_x': True,
            'x_label': 'Avg Drawdown % (lower is better)',
            'y_label': 'Win/Loss Ratio (higher is better)'
        },
        "Run-Up vs Drawdown": {
            'x_axis': 'Avg_Drawdown_Pct',
            'y_axis': 'Max_Run_Up_Pct',
            'size_metric': 'Win_Loss_Ratio',
            'color_metric': 'Equity_Curve_Smoothness',
            'title': 'Max Run-Up vs Avg Drawdown',
            'reverse_x': True,
            'x_label': 'Avg Drawdown % (lower is better)',
            'y_label': 'Max Run-Up % (higher is better)'
        },
        "Risk-Adjusted Performance": {
            'x_axis': 'Max_Drawdown_Pct',
            'y_axis': 'Equity_Curve_Smoothness',
            'size_metric': 'Net_Profit_Pct',
            'color_metric': 'Profit_Factor',
            'title': 'Equity Smoothness vs Max Drawdown',
            'reverse_x': True,
            'x_label': 'Max Drawdown % (lower is better)',
            'y_label': 'Equity Smoothness (higher is better)'
        },
        "Trade Efficiency": {
            'x_axis': 'Avg_Bars_In_Trades',
            'y_axis': 'Trade_Duration_Efficiency',
            'size_metric': 'Net_Profit_Pct',
            'color_metric': 'Win_Loss_Duration_Spread',
            'title': 'Trade Duration Efficiency Analysis',
            'reverse_x': False,
            'x_label': 'Avg Bars in Trades',
            'y_label': 'Trade Duration Efficiency (higher is better)'
        }
    }
    return presets.get(preset_name, presets["Win/Loss Analysis"])

analysis_type = st.selectbox(
    "Select Chart Preset",
    [
        "Win/Loss Analysis",
        "Run-Up vs Drawdown",
        "Risk-Adjusted Performance",
        "Trade Efficiency"
    ],
    help="Choose a preset analysis view or customize axes below"
)

st.markdown("---")

# Filtering Section
st.header("Filters")

# Filter Presets
def get_filter_preset(preset_name):
    """
    Get predefined filter configurations for common analysis scenarios.

    Returns: dict of {metric_name: percentile_value}
    """
    presets = {
        "Balanced (50% All)": {k: 50 for k in metrics_config.keys()},
        "Conservative": {
            'Win_Loss_Ratio': 70, 'Profit_Factor': 70, 'Win_Loss_Spread': 70, 'Loss_Control_Metric': 20,
            'Max_Drawdown_Pct': 20, 'Avg_Drawdown_Pct': 20, 'Tail_Risk': 15, 'Avg_RunUp_DD_Ratio': 70,
            'Equity_Curve_Smoothness': 80, 'Trade_Duration_Efficiency': 60, 'Win_Loss_Duration_Spread': 60,
            'Hedge_Quality_Index': 80, 'Net_Profit_Pct': 60, 'Percent_Profitable': 70, 'Max_Run_Up_Pct': 60,
            'Capital_Leverage_Ratio': 30, 'Capital_Efficiency_Ratio': 70
        },
        "Aggressive": {
            'Win_Loss_Ratio': 50, 'Profit_Factor': 80, 'Win_Loss_Spread': 60, 'Loss_Control_Metric': 50,
            'Max_Drawdown_Pct': 60, 'Avg_Drawdown_Pct': 60, 'Tail_Risk': 50, 'Avg_RunUp_DD_Ratio': 60,
            'Equity_Curve_Smoothness': 50, 'Trade_Duration_Efficiency': 70, 'Win_Loss_Duration_Spread': 50,
            'Hedge_Quality_Index': 50, 'Net_Profit_Pct': 80, 'Percent_Profitable': 50, 'Max_Run_Up_Pct': 80,
            'Capital_Leverage_Ratio': 80, 'Capital_Efficiency_Ratio': 50
        },
        "High Quality": {
            'Win_Loss_Ratio': 80, 'Profit_Factor': 70, 'Win_Loss_Spread': 80, 'Loss_Control_Metric': 20,
            'Max_Drawdown_Pct': 20, 'Avg_Drawdown_Pct': 20, 'Tail_Risk': 20, 'Avg_RunUp_DD_Ratio': 80,
            'Equity_Curve_Smoothness': 80, 'Trade_Duration_Efficiency': 70, 'Win_Loss_Duration_Spread': 70,
            'Hedge_Quality_Index': 80, 'Net_Profit_Pct': 70, 'Percent_Profitable': 70, 'Max_Run_Up_Pct': 70,
            'Capital_Leverage_Ratio': 20, 'Capital_Efficiency_Ratio': 80
        },
        "Low Risk": {
            'Win_Loss_Ratio': 60, 'Profit_Factor': 60, 'Win_Loss_Spread': 60, 'Loss_Control_Metric': 15,
            'Max_Drawdown_Pct': 15, 'Avg_Drawdown_Pct': 15, 'Tail_Risk': 10, 'Avg_RunUp_DD_Ratio': 70,
            'Equity_Curve_Smoothness': 80, 'Trade_Duration_Efficiency': 50, 'Win_Loss_Duration_Spread': 60,
            'Hedge_Quality_Index': 80, 'Net_Profit_Pct': 50, 'Percent_Profitable': 70, 'Max_Run_Up_Pct': 50,
            'Capital_Leverage_Ratio': 20, 'Capital_Efficiency_Ratio': 80
        }
    }
    return presets.get(preset_name, presets["Balanced (50% All)"])

# Filter preset selector
preset_col1, preset_col2 = st.columns([1, 3])
with preset_col1:
    filter_preset = st.selectbox(
        "Filter Preset",
        ["Custom", "Balanced (50% All)", "Conservative", "Aggressive", "High Quality", "Low Risk"],
        help="Load predefined filter configurations for common scenarios"
    )

with preset_col2:
    if filter_preset != "Custom":
        st.info(f"📌 **{filter_preset}** preset loaded. Adjust individual sliders below to customize.")

st.markdown("---")
st.markdown("**Set percentile thresholds for each metric** (higher % = more selective)")

# Create filter columns (4 columns for expanded metrics)
col1, col2, col3, col4 = st.columns(4)

# Define metrics and their filter directions
metrics_config = {
    # Format: 'Column_Name': ('Display Name', 'direction', default_pct, tooltip)
    # direction: 'top' = keep top X%, 'bottom' = keep bottom X%

    # Win/Loss Analysis
    'Win_Loss_Ratio': ('Win/Loss Ratio', 'top', 50, 'Avg Win % / |Avg Loss %|. Higher = wins much larger than losses. Good > 2.0'),
    'Profit_Factor': ('Profit Factor', 'top', 50, 'Gross Profit / Gross Loss. Higher = better. Good > 1.5'),
    'Win_Loss_Spread': ('Win/Loss Spread', 'top', 50, 'Avg Win % - Avg Loss %. Higher = better expectancy'),
    'Loss_Control_Metric': ('Loss Control', 'bottom', 50, 'Avg Loss % / Avg Win %. Lower = better loss control. Good < 0.5'),

    # Risk Management
    'Max_Drawdown_Pct': ('Max Drawdown %', 'bottom', 50, 'Maximum peak-to-trough decline. Lower = better capital preservation'),
    'Avg_Drawdown_Pct': ('Avg Drawdown %', 'bottom', 50, 'Average close-to-close drawdown. Lower = more consistent'),
    'Tail_Risk': ('Tail Risk', 'bottom', 50, 'Largest Loss / Avg Loss. Lower = no extreme outliers. Good < 2.0'),
    'Avg_RunUp_DD_Ratio': ('Avg Run-Up/DD Ratio', 'top', 50, 'Max Run-up / Avg Drawdown. Higher = better upside vs typical DD. Good > 15'),

    # Efficiency & Consistency
    'Equity_Curve_Smoothness': ('Equity Smoothness', 'top', 50, 'Max Run-up / Max Drawdown. Higher = smoother equity curve. Good > 3.0'),
    'Trade_Duration_Efficiency': ('Duration Efficiency', 'top', 50, 'Net Profit % / Avg Bars. Higher = better time usage'),
    'Win_Loss_Duration_Spread': ('Win/Loss Duration Spread', 'top', 50, 'Time efficiency: winning fast vs losing slow. Positive = good'),
    'Hedge_Quality_Index': ('Hedge Quality', 'top', 50, '(1 - Loss/Win) × 100. Higher = better loss management (0-100 scale)'),
    'Capital_Leverage_Ratio': ('Capital Leverage', 'bottom', 50, 'Account Size Required / Initial Capital. Lower = less leverage needed. 1.0 = no leverage'),
    'Capital_Efficiency_Ratio': ('Capital Efficiency', 'top', 50, 'Return / Leverage Ratio. Higher = better return per dollar of capital required'),

    # Overall Performance
    'Net_Profit_Pct': ('Net Profit %', 'top', 50, 'Total return. Higher = better'),
    'Percent_Profitable': ('Win Rate %', 'top', 50, 'Percentage of winning trades. Higher = better'),
    'Max_Run_Up_Pct': ('Max Run-Up %', 'top', 50, 'Maximum peak-to-bottom gain. Higher = strong profit potential'),
}

# Get preset values if selected
preset_values = get_filter_preset(filter_preset) if filter_preset != "Custom" else {}

# Store filter values
filters = {}

with col1:
    st.subheader("Win/Loss Analysis")
    filters['Win_Loss_Ratio'] = st.slider(
        "Win/Loss Ratio (Top)",
        0, 100, preset_values.get('Win_Loss_Ratio', 100), 5,
        help=metrics_config['Win_Loss_Ratio'][3]
    )
    filters['Profit_Factor'] = st.slider(
        "Profit Factor (Top)",
        0, 100, preset_values.get('Profit_Factor', 100), 5,
        help=metrics_config['Profit_Factor'][3]
    )
    filters['Win_Loss_Spread'] = st.slider(
        "Win/Loss Spread (Top)",
        0, 100, preset_values.get('Win_Loss_Spread', 100), 5,
        help=metrics_config['Win_Loss_Spread'][3]
    )
    filters['Loss_Control_Metric'] = st.slider(
        "Loss Control (Bottom)",
        0, 100, preset_values.get('Loss_Control_Metric', 100), 5,
        help=metrics_config['Loss_Control_Metric'][3]
    )

with col2:
    st.subheader("Risk Management")
    filters['Max_Drawdown_Pct'] = st.slider(
        "Max Drawdown % (Bottom)",
        0, 100, preset_values.get('Max_Drawdown_Pct', 100), 5,
        help=metrics_config['Max_Drawdown_Pct'][3]
    )
    filters['Avg_Drawdown_Pct'] = st.slider(
        "Avg Drawdown % (Bottom)",
        0, 100, preset_values.get('Avg_Drawdown_Pct', 100), 5,
        help=metrics_config['Avg_Drawdown_Pct'][3]
    )
    filters['Tail_Risk'] = st.slider(
        "Tail Risk (Bottom)",
        0, 100, preset_values.get('Tail_Risk', 100), 5,
        help=metrics_config['Tail_Risk'][3]
    )
    filters['Avg_RunUp_DD_Ratio'] = st.slider(
        "Avg Run-Up/DD Ratio (Top)",
        0, 100, preset_values.get('Avg_RunUp_DD_Ratio', 100), 5,
        help=metrics_config['Avg_RunUp_DD_Ratio'][3]
    )

with col3:
    st.subheader("Efficiency & Consistency")
    filters['Equity_Curve_Smoothness'] = st.slider(
        "Equity Smoothness (Top)",
        0, 100, preset_values.get('Equity_Curve_Smoothness', 100), 5,
        help=metrics_config['Equity_Curve_Smoothness'][3]
    )
    filters['Trade_Duration_Efficiency'] = st.slider(
        "Duration Efficiency (Top)",
        0, 100, preset_values.get('Trade_Duration_Efficiency', 100), 5,
        help=metrics_config['Trade_Duration_Efficiency'][3]
    )
    filters['Win_Loss_Duration_Spread'] = st.slider(
        "Win/Loss Duration Spread (Top)",
        0, 100, preset_values.get('Win_Loss_Duration_Spread', 100), 5,
        help=metrics_config['Win_Loss_Duration_Spread'][3]
    )
    filters['Hedge_Quality_Index'] = st.slider(
        "Hedge Quality (Top)",
        0, 100, preset_values.get('Hedge_Quality_Index', 100), 5,
        help=metrics_config['Hedge_Quality_Index'][3]
    )
    filters['Capital_Leverage_Ratio'] = st.slider(
        "Capital Leverage (Bottom)",
        0, 100, preset_values.get('Capital_Leverage_Ratio', 100), 5,
        help=metrics_config['Capital_Leverage_Ratio'][3]
    )
    filters['Capital_Efficiency_Ratio'] = st.slider(
        "Capital Efficiency (Top)",
        0, 100, preset_values.get('Capital_Efficiency_Ratio', 100), 5,
        help=metrics_config['Capital_Efficiency_Ratio'][3]
    )

with col4:
    st.subheader("Overall Performance")
    filters['Net_Profit_Pct'] = st.slider(
        "Net Profit % (Top)",
        0, 100, preset_values.get('Net_Profit_Pct', 100), 5,
        help=metrics_config['Net_Profit_Pct'][3]
    )
    filters['Percent_Profitable'] = st.slider(
        "Win Rate % (Top)",
        0, 100, preset_values.get('Percent_Profitable', 100), 5,
        help=metrics_config['Percent_Profitable'][3]
    )
    filters['Max_Run_Up_Pct'] = st.slider(
        "Max Run-Up % (Top)",
        0, 100, preset_values.get('Max_Run_Up_Pct', 100), 5,
        help=metrics_config['Max_Run_Up_Pct'][3]
    )

# Apply Filters Button
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])

with col_btn1:
    apply_filters = st.button("Apply Filters & Graph", type="primary", use_container_width=True)

with col_btn2:
    reset_filters = st.button("Reset", use_container_width=True)

if reset_filters:
    st.rerun()

# Filter and visualize
if apply_filters or 'filtered_df' in st.session_state:

    if apply_filters:
        # Apply percentile filters
        filtered_df = df.copy()

        for metric, pct in filters.items():
            if metric in filtered_df.columns:
                # Get direction from config
                direction = metrics_config[metric][1]

                if direction == 'top':
                    # Keep top X% (higher values)
                    threshold = filtered_df[metric].quantile(1 - pct/100)
                    filtered_df = filtered_df[filtered_df[metric] >= threshold]
                else:  # 'bottom'
                    # Keep bottom X% (lower values, better for drawdown)
                    threshold = filtered_df[metric].quantile(pct/100)
                    filtered_df = filtered_df[filtered_df[metric] <= threshold]

        # Store in session state
        st.session_state['filtered_df'] = filtered_df
    else:
        filtered_df = st.session_state['filtered_df']

    # Show filter results
    st.markdown("---")
    st.subheader(f"Results: {len(filtered_df):,} strategies passed filters ({len(filtered_df)/len(df)*100:.1f}%)")

    # Get chart preset configuration
    preset_config = get_chart_preset_config(analysis_type)

    # Bubble Chart Analysis
    st.markdown(f"### {preset_config['title']}")

    # Chart configuration
    chart_col1, chart_col2 = st.columns([3, 1])

    with chart_col2:
        st.markdown("**Chart Options**")

        # Allow override of preset axes
        st.markdown("*Customize axes (overrides preset):*")

        # X-axis metric
        x_axis_options = [
            'Avg_Drawdown_Pct', 'Max_Drawdown_Pct', 'Avg_Bars_In_Trades',
            'Total_Trades', 'Loss_Control_Metric', 'Tail_Risk'
        ]
        x_axis_default_idx = x_axis_options.index(preset_config['x_axis']) if preset_config['x_axis'] in x_axis_options else 0
        x_axis = st.selectbox(
            "X-Axis",
            x_axis_options,
            index=x_axis_default_idx,
            help="Horizontal axis metric"
        )

        # Y-axis metric
        y_axis_options = [
            'Win_Loss_Ratio', 'Win_Loss_Spread', 'Max_Run_Up_Pct',
            'Risk_Adjusted_CAGR', 'Trade_Duration_Efficiency',
            'Net_Profit_Pct', 'Profit_Factor', 'Equity_Curve_Smoothness'
        ]
        y_axis_default_idx = y_axis_options.index(preset_config['y_axis']) if preset_config['y_axis'] in y_axis_options else 0
        y_axis = st.selectbox(
            "Y-Axis",
            y_axis_options,
            index=y_axis_default_idx,
            help="Vertical axis metric"
        )

        st.markdown("---")

        # Bubble size metric
        size_options = [
            'Total_Trades', 'Win_Loss_Ratio', 'Net_Profit_Pct',
            'Max_Run_Up_Pct', 'Calmar_Ratio', 'Risk_Adjusted_CAGR',
            'Trade_Duration_Efficiency', 'Percent_Profitable',
            'Hedge_Quality_Index', 'Tail_Risk'
        ]
        size_default_idx = size_options.index(preset_config['size_metric']) if preset_config['size_metric'] in size_options else 0
        size_metric = st.selectbox(
            "Bubble Size",
            size_options,
            index=size_default_idx,
            help="What metric determines bubble size"
        )

        # Color metric
        color_options = [
            'Profit_Factor', 'Win_Loss_Ratio', 'Net_Profit_Pct',
            'Calmar_Ratio', 'Equity_Curve_Smoothness',
            'Risk_Adjusted_CAGR', 'Percent_Profitable',
            'Tail_Risk', 'Hedge_Quality_Index', 'Win_Loss_Duration_Spread'
        ]
        color_default_idx = color_options.index(preset_config['color_metric']) if preset_config['color_metric'] in color_options else 0
        color_metric = st.selectbox(
            "Color Metric",
            color_options,
            index=color_default_idx,
            help="What metric determines bubble color"
        )

        # Reverse X-axis option
        reverse_x = st.checkbox(
            "Reverse X-Axis",
            value=preset_config['reverse_x'],
            help="Reverse x-axis (useful for drawdown metrics where lower is better)"
        )

        # Chart height
        chart_height = st.slider("Chart Height", 400, 1000, 600, 50)

        with chart_col1:
            # Create display DataFrame with NA for empty parameter values
            # This prevents empty parameter columns from showing in hover tooltips
            display_df = filtered_df.copy()

            # Parameter columns that may be empty for some strategies (support both formats)
            param_cols = [
                'DC_Length', 'DC_Offset',  # Old format
                'Top_DC_Length', 'Top_DC_Offset', 'Bottom_DC_Length', 'Bottom_DC_Offset',  # New format
                'ATR_Period', 'HHV_Period', 'ATR_Multiplier',
                'TRAMA_Length', 'TRAMA_Lookback'
            ]

            # Replace empty strings with pd.NA (Plotly handles these better)
            for col in param_cols:
                if col in display_df.columns:
                    display_df[col] = display_df[col].replace('', pd.NA)

            # Build hover_data dynamically based on available columns
            hover_data = {
                'Ticker': True,
                'Strategy': True,
                'Total_Trades': True,
                'Net_Profit_Pct': ':.2f',
                'Profit_Factor': ':.2f',
                'Win_Loss_Ratio': ':.2f',
                'Win_Loss_Spread': ':.2f',
                'Avg_Drawdown_Pct': ':.2f',
                'Max_Drawdown_Pct': ':.2f',
                'Max_Run_Up_Pct': ':.2f',
                'Percent_Profitable': ':.2f',
                'Avg_RunUp_DD_Ratio': ':.2f',
                'Trade_Duration_Efficiency': ':.4f',
                'Tail_Risk': ':.2f',
                'Hedge_Quality_Index': ':.2f',
                'Equity_Curve_Smoothness': ':.2f',
                'Loss_Control_Metric': ':.2f',
                'Win_Loss_Duration_Spread': ':.4f'
            }

            # Add parameter columns (these will be filtered by strategy type next in Phase 4)
            param_hover = {
                'ATR_Period': True,
                'HHV_Period': True,
                'ATR_Multiplier': ':.2f',
            }
            hover_data.update(param_hover)

            # Add Donchian columns (always relevant for both DC_ONLY and FULL_SIGIL)
            if 'DC_Length' in display_df.columns:
                hover_data['DC_Length'] = True
            if 'DC_Offset' in display_df.columns:
                hover_data['DC_Offset'] = True
            if 'Top_DC_Length' in display_df.columns:
                hover_data['Top_DC_Length'] = True
            if 'Top_DC_Offset' in display_df.columns:
                hover_data['Top_DC_Offset'] = True
            if 'Bottom_DC_Length' in display_df.columns:
                hover_data['Bottom_DC_Length'] = True
            if 'Bottom_DC_Offset' in display_df.columns:
                hover_data['Bottom_DC_Offset'] = True

            # Add TRAMA columns (only show if ANY row uses them - will be hidden for pure DC_ONLY datasets)
            if 'TRAMA_Length' in display_df.columns:
                # Check if TRAMA is actually used
                if display_df['TRAMA_Length'].notna().any() and (display_df['TRAMA_Length'] != '').any() and (display_df['TRAMA_Length'] != 0).any():
                    hover_data['TRAMA_Length'] = True
            if 'TRAMA_Lookback' in display_df.columns:
                if display_df['TRAMA_Lookback'].notna().any() and (display_df['TRAMA_Lookback'] != '').any() and (display_df['TRAMA_Lookback'] != 0).any():
                    hover_data['TRAMA_Lookback'] = True

            # Add MACD Slope parameters (if they exist)
            macd_params = [
                '__Use_MACD_Slope', '__Source', '__Fast_Length', '__Slow_Length',
                '__Signal_Length', '__Histogram_Smoothing_SMA', '__Slope_Lookback_bars',
                '__Entry_Slope_Threshold', '__Exit_Slope_Threshold', '__MACD_Slope_Hold_Pct'
            ]
            for param in macd_params:
                if param in display_df.columns:
                    if display_df[param].notna().any() and (display_df[param] != '').any():
                        if param in ['__Entry_Slope_Threshold', '__Exit_Slope_Threshold', '__MACD_Slope_Hold_Pct']:
                            hover_data[param] = ':.2f'
                        else:
                            hover_data[param] = True

            # Add RSI Slope parameters (if they exist)
            rsi_params = [
                '__Use_RSI_Slope', '__RSI_Length', '__Smoothing_Type',
                '__Smoothing_Length', '__RSI_Slope_Hold_Pct'
            ]
            for param in rsi_params:
                if param in display_df.columns:
                    if display_df[param].notna().any() and (display_df[param] != '').any():
                        if param == '__RSI_Slope_Hold_Pct':
                            hover_data[param] = ':.2f'
                        else:
                            hover_data[param] = True

            # Add Hold % parameters (if they exist)
            hold_params = ['__Donchian_Channel_Hold_Pct', '__Trailing_Stop_Hold_Pct']
            for param in hold_params:
                if param in display_df.columns:
                    if display_df[param].notna().any() and (display_df[param] != '').any():
                        hover_data[param] = ':.2f'

            # Filter hover_data to only include columns that exist in display_df
            hover_data = {k: v for k, v in hover_data.items() if k in display_df.columns}

            # Create bubble chart with dynamic axes
            fig = px.scatter(
                display_df,
                x=x_axis,
                y=y_axis,
                size=size_metric,
                color=color_metric,
                hover_data=hover_data,
                labels={
                    x_axis: x_axis.replace('_', ' '),
                    y_axis: y_axis.replace('_', ' '),
                    size_metric: size_metric.replace('_', ' '),
                    color_metric: color_metric.replace('_', ' ')
                },
                title=f"{y_axis.replace('_', ' ')} vs {x_axis.replace('_', ' ')} ({len(filtered_df)} strategies)",
                color_continuous_scale='RdYlGn',
                height=chart_height
            )

            # Determine axis labels (use preset if using preset axes, otherwise generic)
            x_label = preset_config['x_label'] if x_axis == preset_config['x_axis'] else f"{x_axis.replace('_', ' ')}"
            y_label = preset_config['y_label'] if y_axis == preset_config['y_axis'] else f"{y_axis.replace('_', ' ')}"

            # Update layout
            fig.update_layout(
                xaxis_title=x_label,
                yaxis_title=y_label,
                hovermode='closest',
                font=dict(size=12)
            )

            # Reverse x-axis if requested
            if reverse_x:
                fig.update_xaxes(autorange="reversed")

            # Add quadrant lines (if data exists)
            if len(filtered_df) > 0 and x_axis in filtered_df.columns and y_axis in filtered_df.columns:
                median_x = filtered_df[x_axis].median()
                median_y = filtered_df[y_axis].median()

                # Vertical line at median x
                fig.add_vline(
                    x=median_x,
                    line_dash="dash",
                    line_color="gray",
                    opacity=0.5,
                    annotation_text=f"Median {x_axis.replace('_', ' ')}: {median_x:.2f}",
                    annotation_position="top"
                )

                # Horizontal line at median y
                fig.add_hline(
                    y=median_y,
                    line_dash="dash",
                    line_color="gray",
                    opacity=0.5,
                    annotation_text=f"Median {y_axis.replace('_', ' ')}: {median_y:.2f}",
                    annotation_position="right"
                )

            st.plotly_chart(fig, use_container_width=True)

        # Top performers table
        st.markdown("---")
        st.subheader("Top 10 Performers (by Net Profit)")

        # Build column list dynamically based on strategy type and available columns
        top_10_cols = ['Ticker', 'Strategy', 'Strategy_Type']

        # Add Donchian columns if they exist (relevant for all strategies)
        if 'DC_Length' in filtered_df.columns:
            top_10_cols.extend(['DC_Length', 'DC_Offset'])
        if 'Top_DC_Length' in filtered_df.columns:
            top_10_cols.extend(['Top_DC_Length', 'Top_DC_Offset', 'Bottom_DC_Length', 'Bottom_DC_Offset'])

        # Check if dataset contains FULL_SIGIL strategies (add optional params if so)
        has_full_sigil = False
        if 'Strategy_Type' in filtered_df.columns:
            has_full_sigil = (filtered_df['Strategy_Type'] == 'FULL_SIGIL').any() or (filtered_df['Strategy_Type'] == 'PARTIAL').any()

        if has_full_sigil:
            # Add optional parameters (only if FULL_SIGIL strategies present)
            optional_params = ['ATR_Period', 'HHV_Period', 'ATR_Multiplier', 'TRAMA_Length', 'TRAMA_Lookback']
            for param in optional_params:
                if param in filtered_df.columns:
                    top_10_cols.append(param)

        # Add key performance metrics
        top_10_cols.extend([
            'Net_Profit_Pct', 'Win_Loss_Ratio', 'Max_Drawdown_Pct',
            'Avg_Drawdown_Pct', 'Profit_Factor', 'Total_Trades',
            'Percent_Profitable', 'Risk_Adjusted_CAGR'
        ])

        # Filter to only include columns that exist
        top_10_cols = [col for col in top_10_cols if col in filtered_df.columns]

        top_10 = filtered_df.nlargest(10, 'Net_Profit_Pct')[top_10_cols].round(2)

        st.dataframe(top_10, use_container_width=True, hide_index=True)

        # Export options
        st.markdown("---")
        st.subheader("Export Options")

        export_col1, export_col2 = st.columns(2)

        with export_col1:
            # CSV export
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download Filtered Results (CSV)",
                data=csv,
                file_name=f"scry_filtered_{len(filtered_df)}_results.csv",
                mime="text/csv",
                use_container_width=True
            )

        with export_col2:
            # Chart export instructions
            st.info("**Save Chart as PNG**: Hover over chart and click camera icon")

# Footer
st.markdown("---")
st.caption("SIGIL Quantitative | SCRY Backtesting Analysis Dashboard")
