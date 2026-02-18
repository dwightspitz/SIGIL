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
    """Load and cache the CSV data - handles any TradingView export format"""
    df = pd.read_csv(file)

    # Auto-detect and standardize column names from any TradingView export
    # This uses pattern matching to handle variations in column naming

    # Build dynamic column mapping based on what's in the CSV
    column_mapping = {}

    for col in df.columns:
        col_lower = col.lower()

        # Performance Metrics - prefer ": All" versions, fall back to base
        if 'net p&l %' in col_lower or 'net profit %' in col_lower:
            if ': all' in col_lower or col_lower.endswith('net p&l %') or col_lower.endswith('net profit %'):
                column_mapping[col] = 'Net_Profit_Pct'
        elif 'total trades' in col_lower or 'total closed trades' in col_lower:
            if ': all' in col_lower or 'total trades' == col_lower or 'total closed trades' == col_lower:
                column_mapping[col] = 'Total_Trades'
        elif 'percent profitable' in col_lower:
            if ': all' in col_lower or col_lower == 'percent profitable':
                column_mapping[col] = 'Percent_Profitable'
        elif 'profit factor' in col_lower:
            if ': all' in col_lower or col_lower == 'profit factor':
                column_mapping[col] = 'Profit_Factor'

        # Drawdown Metrics
        elif 'max' in col_lower and 'drawdown' in col_lower and '%' in col_lower:
            column_mapping[col] = 'Max_Drawdown_Pct'
        elif 'avg' in col_lower and 'drawdown' in col_lower and '%' in col_lower:
            column_mapping[col] = 'Avg_Drawdown_Pct'

        # Run-up Metrics
        elif 'max' in col_lower and 'run-up' in col_lower and '%' in col_lower:
            column_mapping[col] = 'Max_Run_Up_Pct'

        # Trade Metrics
        elif ('avg p&l %' in col_lower or 'avg trade %' in col_lower):
            if ': all' in col_lower or col_lower in ['avg p&l %', 'avg trade %']:
                column_mapping[col] = 'Avg_Trade_Pct'
        elif 'avg' in col_lower and 'bars in trades' in col_lower:
            if ': all' in col_lower or col_lower == 'avg # bars in trades':
                column_mapping[col] = 'Avg_Bars_In_Trades'

        # Winning Trade Metrics
        elif 'avg winning trade' in col_lower and '%' in col_lower:
            if ': all' in col_lower or col_lower == 'avg winning trade %':
                column_mapping[col] = 'Avg_Winning_Trade_Pct'
        elif 'avg' in col_lower and 'bars in winning' in col_lower:
            if ': all' in col_lower or 'winning trades' in col_lower:
                column_mapping[col] = 'Avg_Bars_In_Winning_Trades'

        # Losing Trade Metrics
        elif 'avg losing trade' in col_lower and '%' in col_lower:
            if ': all' in col_lower or col_lower == 'avg losing trade %':
                column_mapping[col] = 'Avg_Losing_Trade_Pct'
        elif 'avg' in col_lower and 'bars in losing' in col_lower:
            if ': all' in col_lower or 'losing trades' in col_lower:
                column_mapping[col] = 'Avg_Bars_In_Losing_Trades'

        # Extreme Trade Metrics
        elif 'largest winning' in col_lower and '%' in col_lower:
            if ': all' in col_lower or 'percent' in col_lower:
                column_mapping[col] = 'Largest_Winning_Trade_Pct'
        elif 'largest losing' in col_lower and '%' in col_lower:
            if ': all' in col_lower or 'percent' in col_lower:
                column_mapping[col] = 'Largest_Losing_Trade_Pct'

        # Benchmark
        elif 'buy & hold' in col_lower or 'buy and hold' in col_lower:
            column_mapping[col] = 'Buy_And_Hold_Return_Pct'

        # Capital Efficiency Metrics
        elif col_lower == 'account size required':
            column_mapping[col] = 'Account_Size_Required'
        elif 'return on account size' in col_lower:
            column_mapping[col] = 'Return_On_Account_Size_Required'

        # Strategy Parameters (columns starting with __)
        # These are auto-detected and cleaned up
        elif col.startswith('__'):
            # Clean parameter name: remove __ prefix, replace spaces with _, handle special chars
            clean_name = col.replace(' ', '_').replace('(', '').replace(')', '').replace('°', '')
            column_mapping[col] = clean_name

    # Rename columns that were mapped
    df = df.rename(columns=column_mapping)

    # Remove duplicate columns (keep first occurrence)
    # This handles cases where TradingView exports both base columns and ": All" versions
    df = df.loc[:, ~df.columns.duplicated(keep='first')]

    # Calculate derived metrics (only for columns that exist)
    df = calculate_derived_metrics(df)

    # Detect strategy types
    df = detect_strategy_type(df)

    return df

try:
    df = load_data(uploaded_file)

    # Set available metrics based on loaded data
    metrics_config = get_available_metrics(df)

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

# Column Detection Info
with st.expander("📋 Detected Columns", expanded=False):
    col_info1, col_info2, col_info3 = st.columns(3)

    # Categorize detected columns
    metric_cols = [col for col in df.columns if col in ALL_METRICS_CONFIG or col in metrics_config]
    param_cols = [col for col in df.columns if col.startswith('__') or any(p in col for p in ['DC_', 'ATR_', 'TRAMA_', 'HHV_', 'Length', 'Offset'])]
    other_cols = [col for col in df.columns if col not in metric_cols and col not in param_cols]

    with col_info1:
        st.markdown("**Performance Metrics**")
        st.write(", ".join(metric_cols) if metric_cols else "None detected")

    with col_info2:
        st.markdown("**Strategy Parameters**")
        st.write(", ".join(param_cols) if param_cols else "None detected")

    with col_info3:
        st.markdown("**Other Columns**")
        st.write(", ".join(other_cols[:15]) + ("..." if len(other_cols) > 15 else "") if other_cols else "None")

    st.caption(f"Total: {len(df.columns)} columns detected")

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
    Only returns values for metrics that exist in the current metrics_config.

    Returns: dict of {metric_name: percentile_value}
    """
    # Base presets with all possible metrics
    all_presets = {
        "Balanced (50% All)": {k: 50 for k in ALL_METRICS_CONFIG.keys()},
        "Conservative": {
            'Win_Loss_Ratio': 70, 'Profit_Factor': 70, 'Win_Loss_Spread': 70, 'Loss_Control_Metric': 20,
            'Max_Drawdown_Pct': 20, 'Avg_Drawdown_Pct': 20, 'Tail_Risk': 15, 'Avg_RunUp_DD_Ratio': 70,
            'Equity_Curve_Smoothness': 80, 'Trade_Duration_Efficiency': 60, 'Win_Loss_Duration_Spread': 60,
            'Hedge_Quality_Index': 80, 'Net_Profit_Pct': 60, 'Percent_Profitable': 70, 'Max_Run_Up_Pct': 60,
            'Capital_Leverage_Ratio': 30, 'Capital_Efficiency_Ratio': 70, 'Total_Trades': 50
        },
        "Aggressive": {
            'Win_Loss_Ratio': 50, 'Profit_Factor': 80, 'Win_Loss_Spread': 60, 'Loss_Control_Metric': 50,
            'Max_Drawdown_Pct': 60, 'Avg_Drawdown_Pct': 60, 'Tail_Risk': 50, 'Avg_RunUp_DD_Ratio': 60,
            'Equity_Curve_Smoothness': 50, 'Trade_Duration_Efficiency': 70, 'Win_Loss_Duration_Spread': 50,
            'Hedge_Quality_Index': 50, 'Net_Profit_Pct': 80, 'Percent_Profitable': 50, 'Max_Run_Up_Pct': 80,
            'Capital_Leverage_Ratio': 80, 'Capital_Efficiency_Ratio': 50, 'Total_Trades': 50
        },
        "High Quality": {
            'Win_Loss_Ratio': 80, 'Profit_Factor': 70, 'Win_Loss_Spread': 80, 'Loss_Control_Metric': 20,
            'Max_Drawdown_Pct': 20, 'Avg_Drawdown_Pct': 20, 'Tail_Risk': 20, 'Avg_RunUp_DD_Ratio': 80,
            'Equity_Curve_Smoothness': 80, 'Trade_Duration_Efficiency': 70, 'Win_Loss_Duration_Spread': 70,
            'Hedge_Quality_Index': 80, 'Net_Profit_Pct': 70, 'Percent_Profitable': 70, 'Max_Run_Up_Pct': 70,
            'Capital_Leverage_Ratio': 20, 'Capital_Efficiency_Ratio': 80, 'Total_Trades': 50
        },
        "Low Risk": {
            'Win_Loss_Ratio': 60, 'Profit_Factor': 60, 'Win_Loss_Spread': 60, 'Loss_Control_Metric': 15,
            'Max_Drawdown_Pct': 15, 'Avg_Drawdown_Pct': 15, 'Tail_Risk': 10, 'Avg_RunUp_DD_Ratio': 70,
            'Equity_Curve_Smoothness': 80, 'Trade_Duration_Efficiency': 50, 'Win_Loss_Duration_Spread': 60,
            'Hedge_Quality_Index': 80, 'Net_Profit_Pct': 50, 'Percent_Profitable': 70, 'Max_Run_Up_Pct': 50,
            'Capital_Leverage_Ratio': 20, 'Capital_Efficiency_Ratio': 80, 'Total_Trades': 50
        }
    }

    preset = all_presets.get(preset_name, all_presets["Balanced (50% All)"])

    # Filter to only include metrics that exist in current metrics_config
    return {k: v for k, v in preset.items() if k in metrics_config}

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

# Define ALL possible metrics and their filter directions
# These will be filtered to only show metrics that exist in the uploaded data
ALL_METRICS_CONFIG = {
    # Format: 'Column_Name': ('Display Name', 'direction', default_pct, tooltip, category)
    # direction: 'top' = keep top X%, 'bottom' = keep bottom X%

    # Win/Loss Analysis
    'Win_Loss_Ratio': ('Win/Loss Ratio', 'top', 50, 'Avg Win % / |Avg Loss %|. Higher = wins much larger than losses. Good > 2.0', 'Win/Loss Analysis'),
    'Profit_Factor': ('Profit Factor', 'top', 50, 'Gross Profit / Gross Loss. Higher = better. Good > 1.5', 'Win/Loss Analysis'),
    'Win_Loss_Spread': ('Win/Loss Spread', 'top', 50, 'Avg Win % - Avg Loss %. Higher = better expectancy', 'Win/Loss Analysis'),
    'Loss_Control_Metric': ('Loss Control', 'bottom', 50, 'Avg Loss % / Avg Win %. Lower = better loss control. Good < 0.5', 'Win/Loss Analysis'),

    # Risk Management
    'Max_Drawdown_Pct': ('Max Drawdown %', 'bottom', 50, 'Maximum peak-to-trough decline. Lower = better capital preservation', 'Risk Management'),
    'Avg_Drawdown_Pct': ('Avg Drawdown %', 'bottom', 50, 'Average close-to-close drawdown. Lower = more consistent', 'Risk Management'),
    'Tail_Risk': ('Tail Risk', 'bottom', 50, 'Largest Loss / Avg Loss. Lower = no extreme outliers. Good < 2.0', 'Risk Management'),
    'Avg_RunUp_DD_Ratio': ('Avg Run-Up/DD Ratio', 'top', 50, 'Max Run-up / Avg Drawdown. Higher = better upside vs typical DD. Good > 15', 'Risk Management'),

    # Efficiency & Consistency
    'Equity_Curve_Smoothness': ('Equity Smoothness', 'top', 50, 'Max Run-up / Max Drawdown. Higher = smoother equity curve. Good > 3.0', 'Efficiency'),
    'Trade_Duration_Efficiency': ('Duration Efficiency', 'top', 50, 'Net Profit % / Avg Bars. Higher = better time usage', 'Efficiency'),
    'Win_Loss_Duration_Spread': ('Win/Loss Duration Spread', 'top', 50, 'Time efficiency: winning fast vs losing slow. Positive = good', 'Efficiency'),
    'Hedge_Quality_Index': ('Hedge Quality', 'top', 50, '(1 - Loss/Win) × 100. Higher = better loss management (0-100 scale)', 'Efficiency'),
    'Capital_Leverage_Ratio': ('Capital Leverage', 'bottom', 50, 'Account Size Required / Initial Capital. Lower = less leverage needed. 1.0 = no leverage', 'Efficiency'),
    'Capital_Efficiency_Ratio': ('Capital Efficiency', 'top', 50, 'Return / Leverage Ratio. Higher = better return per dollar of capital required', 'Efficiency'),

    # Overall Performance
    'Net_Profit_Pct': ('Net Profit %', 'top', 50, 'Total return. Higher = better', 'Performance'),
    'Percent_Profitable': ('Win Rate %', 'top', 50, 'Percentage of winning trades. Higher = better', 'Performance'),
    'Max_Run_Up_Pct': ('Max Run-Up %', 'top', 50, 'Maximum peak-to-bottom gain. Higher = strong profit potential', 'Performance'),
    'Total_Trades': ('Total Trades', 'top', 50, 'Number of closed trades. Higher = more opportunities', 'Performance'),
}

# Filter to only include metrics that exist in the loaded dataframe
def get_available_metrics(df):
    """Return metrics_config filtered to only metrics present in the dataframe"""
    return {k: v for k, v in ALL_METRICS_CONFIG.items() if k in df.columns}

# Will be set after data is loaded
metrics_config = {}

# Get preset values if selected
preset_values = get_filter_preset(filter_preset) if filter_preset != "Custom" else {}

# Store filter values
filters = {}

# Group metrics by category for display
def group_metrics_by_category(metrics_cfg):
    """Group available metrics by their category"""
    categories = {}
    for metric, config in metrics_cfg.items():
        category = config[4] if len(config) > 4 else 'Other'
        if category not in categories:
            categories[category] = []
        categories[category].append((metric, config))
    return categories

grouped_metrics = group_metrics_by_category(metrics_config)

# Display metrics dynamically based on what's available
# Use up to 4 columns, distributing categories evenly
category_names = list(grouped_metrics.keys())
num_categories = len(category_names)

if num_categories == 0:
    st.warning("No filterable metrics detected in the uploaded CSV. Please check the file format.")
else:
    # Create columns based on number of categories (max 4)
    num_cols = min(4, num_categories)
    cols = st.columns(num_cols)

    # Distribute categories across columns
    for i, (category, metrics_list) in enumerate(grouped_metrics.items()):
        col_idx = i % num_cols
        with cols[col_idx]:
            st.subheader(category)
            for metric, config in metrics_list:
                display_name = config[0]
                direction = config[1]
                tooltip = config[3]
                direction_label = "(Top)" if direction == 'top' else "(Bottom)"

                filters[metric] = st.slider(
                    f"{display_name} {direction_label}",
                    0, 100, preset_values.get(metric, 100), 5,
                    help=tooltip,
                    key=f"filter_{metric}"
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

        # Get numeric columns available for charting
        numeric_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()

        # Filter to meaningful metrics (exclude index-like columns)
        chart_cols = [col for col in numeric_cols if not col.startswith('Unnamed')]

        # X-axis metric - prefer preset if available, otherwise use first available
        x_axis_default = preset_config['x_axis'] if preset_config['x_axis'] in chart_cols else (chart_cols[0] if chart_cols else None)
        x_axis_default_idx = chart_cols.index(x_axis_default) if x_axis_default in chart_cols else 0
        x_axis = st.selectbox(
            "X-Axis",
            chart_cols,
            index=x_axis_default_idx,
            help="Horizontal axis metric"
        )

        # Y-axis metric
        y_axis_default = preset_config['y_axis'] if preset_config['y_axis'] in chart_cols else (chart_cols[1] if len(chart_cols) > 1 else chart_cols[0] if chart_cols else None)
        y_axis_default_idx = chart_cols.index(y_axis_default) if y_axis_default in chart_cols else 0
        y_axis = st.selectbox(
            "Y-Axis",
            chart_cols,
            index=y_axis_default_idx,
            help="Vertical axis metric"
        )

        st.markdown("---")

        # Bubble size metric
        size_default = preset_config['size_metric'] if preset_config['size_metric'] in chart_cols else (chart_cols[2] if len(chart_cols) > 2 else chart_cols[0] if chart_cols else None)
        size_default_idx = chart_cols.index(size_default) if size_default in chart_cols else 0
        size_metric = st.selectbox(
            "Bubble Size",
            chart_cols,
            index=size_default_idx,
            help="What metric determines bubble size"
        )

        # Color metric
        color_default = preset_config['color_metric'] if preset_config['color_metric'] in chart_cols else (chart_cols[3] if len(chart_cols) > 3 else chart_cols[0] if chart_cols else None)
        color_default_idx = chart_cols.index(color_default) if color_default in chart_cols else 0
        color_metric = st.selectbox(
            "Color Metric",
            chart_cols,
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

            # Build hover_data dynamically based on ALL available columns
            hover_data = {}

            # Add all columns to hover, with appropriate formatting
            for col in display_df.columns:
                if col in [x_axis, y_axis, size_metric, color_metric]:
                    # Skip axes columns (already shown)
                    continue
                if col.startswith('Unnamed'):
                    # Skip unnamed index columns
                    continue

                # Determine format based on column type and name
                if display_df[col].dtype in ['float64', 'float32']:
                    # Check if values are small (efficiency metrics) or large (percentages)
                    if display_df[col].abs().max() < 1:
                        hover_data[col] = ':.4f'
                    else:
                        hover_data[col] = ':.2f'
                elif display_df[col].dtype in ['int64', 'int32']:
                    hover_data[col] = True
                elif display_df[col].dtype == 'object':
                    # String columns - only include if they have meaningful values
                    if display_df[col].notna().any() and (display_df[col] != '').any():
                        hover_data[col] = True

            # Limit hover_data to most relevant columns (avoid overwhelming tooltips)
            # Prioritize: identifiers, performance metrics, parameters
            priority_cols = [
                'Ticker', 'Strategy', 'Strategy_Type',
                'Net_Profit_Pct', 'Total_Trades', 'Profit_Factor',
                'Win_Loss_Ratio', 'Max_Drawdown_Pct', 'Percent_Profitable'
            ]

            # Start with priority columns that exist
            limited_hover = {}
            for col in priority_cols:
                if col in hover_data:
                    limited_hover[col] = hover_data[col]

            # Add parameter columns (columns starting with __ or known param names)
            param_patterns = ['__', 'DC_', 'ATR_', 'TRAMA_', 'HHV_', 'Length', 'Offset', 'Period']
            for col in hover_data:
                if any(pat in col for pat in param_patterns):
                    limited_hover[col] = hover_data[col]

            # Add remaining metrics (up to reasonable limit)
            for col in hover_data:
                if col not in limited_hover and len(limited_hover) < 25:
                    limited_hover[col] = hover_data[col]

            hover_data = limited_hover

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

        # Determine best sort column (prefer Net_Profit_Pct, fall back to first numeric)
        sort_col = 'Net_Profit_Pct' if 'Net_Profit_Pct' in filtered_df.columns else chart_cols[0] if chart_cols else None

        if sort_col:
            st.subheader(f"Top 10 Performers (by {sort_col.replace('_', ' ')})")

            # Build column list dynamically - prioritize identifier and parameter columns
            top_10_cols = []

            # Add identifier columns first
            id_cols = ['Ticker', 'Strategy', 'Strategy_Type']
            for col in id_cols:
                if col in filtered_df.columns:
                    top_10_cols.append(col)

            # Add all parameter columns (columns starting with __ or known param patterns)
            param_patterns = ['__', 'DC_', 'ATR_', 'TRAMA_', 'HHV_', 'Length', 'Offset', 'Period', 'Multiplier']
            for col in filtered_df.columns:
                if any(pat in col for pat in param_patterns) and col not in top_10_cols:
                    top_10_cols.append(col)

            # Add key performance metrics that exist
            perf_cols = [
                'Net_Profit_Pct', 'Win_Loss_Ratio', 'Max_Drawdown_Pct',
                'Avg_Drawdown_Pct', 'Profit_Factor', 'Total_Trades',
                'Percent_Profitable', 'Equity_Curve_Smoothness',
                'Trade_Duration_Efficiency', 'Max_Run_Up_Pct'
            ]
            for col in perf_cols:
                if col in filtered_df.columns and col not in top_10_cols:
                    top_10_cols.append(col)

            top_10 = filtered_df.nlargest(10, sort_col)[top_10_cols].round(2)

            st.dataframe(top_10, use_container_width=True, hide_index=True)
        else:
            st.warning("No numeric columns available for ranking.")

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
