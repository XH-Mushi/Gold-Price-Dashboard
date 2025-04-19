import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta


def show_gold_chart(gold_df):
    """
    Display gold price chart with different time ranges

    Parameters:
    gold_df (DataFrame): Gold price data with Date and Close columns
    """
    if gold_df is None or gold_df.empty:
        st.error("No gold price data available for charting")
        return

    st.subheader("Gold Price Trend")

    # Add time range selector
    time_range = st.radio(
        "Select time range:",
        ["Recent 3 Months", "Recent 6 Months", "Recent 1 Year", "All Data"],
        horizontal=True
    )

    # Calculate date filters based on selection
    end_date = gold_df['Date'].max()

    if time_range == "Recent 3 Months":
        start_date = end_date - timedelta(days=90)
    elif time_range == "Recent 6 Months":
        start_date = end_date - timedelta(days=180)
    elif time_range == "Recent 1 Year":
        start_date = end_date - timedelta(days=365)
    else:  # All Data
        start_date = gold_df['Date'].min()

    # Filter data based on selected range
    filtered_df = gold_df[gold_df['Date'] >= start_date].copy()

    if filtered_df.empty:
        st.warning("No data available for the selected time range")
        return

    # Create the chart
    try:
        fig, ax = plt.subplots(figsize=(10, 6))

        # Get dates and prices as native Python lists
        dates = filtered_df['Date'].tolist()
        prices = []

        # Extract close prices safely
        for idx in range(len(filtered_df)):
            price = filtered_df['Close'].iloc[idx]
            # Handle if price is a Series
            if isinstance(price, pd.Series):
                price = price.iloc[0]
            prices.append(price)

        # Plot the data
        ax.plot(dates, prices, 'b-', linewidth=2)

        # Format the chart
        ax.set_title(f'Gold Price ({time_range})', fontsize=16)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price (USD)', fontsize=12)
        ax.grid(True, alpha=0.3)

        # Format x-axis dates
        if time_range == "Recent 3 Months":
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        elif time_range == "Recent 6 Months":
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        else:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Show the chart
        st.pyplot(fig)

        # Show price statistics
        st.subheader("Price Statistics")

        # Calculate metrics
        start_price = prices[0]
        end_price = prices[-1]
        price_change = end_price - start_price
        price_change_pct = (price_change / start_price *
                            100) if start_price != 0 else 0

        # Create two columns for metrics
        col1, col2 = st.columns(2)

        # Show metrics in columns
        col1.metric(
            label="Start Price",
            value=f"${start_price:,.2f}"
        )

        col2.metric(
            label="End Price",
            value=f"${end_price:,.2f}",
            delta=f"{price_change_pct:+.2f}%"
        )

    except Exception as e:
        st.error(f"Error generating chart: {str(e)}")
        st.exception(e)
