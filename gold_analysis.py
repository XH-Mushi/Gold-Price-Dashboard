import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime


@st.cache_data
def get_gold_data():
    try:
        # Download gold price data
        gold = yf.download('GC=F', start='2023-01-01',
                           end=datetime.now().strftime('%Y-%m-%d'))

        if gold is None or gold.empty:
            st.warning("No gold data available")
            return None

        # Reset index to make Date a column
        gold.reset_index(inplace=True)
        return gold
    except Exception as e:
        st.error(f"Error getting gold data: {str(e)}")
        return None


def show_gold_analysis():
    # Get the gold data
    gold_df = get_gold_data()

    # Check if data is valid
    if gold_df is None:
        st.error(
            "Unable to get gold price data. Please check your internet connection or try again later.")
        return

    # Display header
    st.header("🌍 Global Gold Price Analysis")

    try:
        # Show most recent close price as current price
        if len(gold_df) > 0:
            # Simple metrics that don't require complex calculations
            last_row = gold_df.iloc[-1]

            if len(gold_df) > 1:
                prev_row = gold_df.iloc[-2]

                # Calculate price change percentage
                price_change_pct = 0
                try:
                    current_price = last_row['Close']
                    prev_price = prev_row['Close']
                    price_change_pct = (
                        current_price - prev_price) / prev_price * 100 if prev_price != 0 else 0
                except:
                    pass

                # Display metrics
                st.subheader("Current Gold Price")
                st.metric(
                    label="Price (USD)",
                    value=f"${last_row['Close']:,.2f}",
                    delta=f"{price_change_pct:+.2f}%"
                )

            # Show latest data in a table
            st.subheader("Recent Gold Prices")

            # Only include important columns
            display_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            recent_data = gold_df.tail(10)[display_cols].copy()

            # Convert dates to string to avoid display issues
            recent_data['Date'] = recent_data['Date'].dt.strftime('%Y-%m-%d')

            # Show the data
            st.dataframe(recent_data, use_container_width=True)

            # Add info about the entire dataset
            st.info(
                f"Total data points: {len(gold_df)} from {gold_df['Date'].min().strftime('%Y-%m-%d')} to {gold_df['Date'].max().strftime('%Y-%m-%d')}")

            # Allow viewing the full dataset
            with st.expander("View all gold price data"):
                st.write("Full dataset:")

                # Clone data and format date
                full_data = gold_df[display_cols].copy()
                full_data['Date'] = full_data['Date'].dt.strftime('%Y-%m-%d')

                st.dataframe(full_data, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing gold data: {str(e)}")
        st.exception(e)
