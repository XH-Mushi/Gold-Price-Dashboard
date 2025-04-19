import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime
import numpy as np


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
    # Get gold data
    gold_df = get_gold_data()

    if gold_df is None:
        st.error(
            "Unable to get gold price data. Please check your internet connection or try again later.")
        return

    st.header("🌍 Global Gold Price Analysis")

    try:
        # Make sure the DataFrame is not empty and has enough rows
        if len(gold_df) < 2:
            st.warning("Not enough data for analysis")
            return

        # Calculate current price and change
        try:
            current_price = gold_df['Close'].iloc[-1]
            previous_price = gold_df['Close'].iloc[-2]

            if isinstance(current_price, pd.Series):
                current_price = current_price.iloc[0]
            if isinstance(previous_price, pd.Series):
                previous_price = previous_price.iloc[0]

            price_change = ((current_price - previous_price) /
                            previous_price * 100) if previous_price != 0 else 0
        except Exception as e:
            st.warning(f"Could not calculate current price metrics: {str(e)}")
            current_price = 0
            price_change = 0

        # Calculate average prices
        try:
            if len(gold_df) >= 30:
                avg_30d = pd.Series(gold_df['Close'].tail(30).values).mean()

                if len(gold_df) >= 60:
                    avg_60d = pd.Series(gold_df['Close'].tail(
                        60).head(30).values).mean()
                else:
                    remaining = len(gold_df) - 30
                    if remaining > 0:
                        avg_60d = pd.Series(
                            gold_df['Close'].head(remaining).values).mean()
                    else:
                        avg_60d = avg_30d

                avg_change = ((avg_30d - avg_60d) / avg_60d *
                              100) if avg_60d != 0 else 0
            else:
                avg_30d = None
                avg_change = None
        except Exception as e:
            st.warning(f"Could not calculate average price metrics: {str(e)}")
            avg_30d = None
            avg_change = None

        # Calculate high/low prices
        try:
            high_price = gold_df['High'].max()
            low_price = gold_df['Low'].min()

            if isinstance(high_price, pd.Series):
                high_price = high_price.iloc[0]
            if isinstance(low_price, pd.Series):
                low_price = low_price.iloc[0]

            range_percent = ((high_price - low_price) /
                             low_price * 100) if low_price != 0 else 0
        except Exception as e:
            st.warning(f"Could not calculate high/low price metrics: {str(e)}")
            high_price = 0
            range_percent = 0

        # Display metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Current Gold Price",
                value=f"${current_price:,.2f}",
                delta=f"{price_change:+.2f}%"
            )

        with col2:
            if avg_30d is not None:
                st.metric(
                    label="30-Day Average Price",
                    value=f"${avg_30d:,.2f}",
                    delta=f"{avg_change:+.2f}%"
                )
            else:
                st.warning("Not enough data for 30-day average")

        with col3:
            st.metric(
                label="Yearly High Price",
                value=f"${high_price:,.2f}",
                delta=f"{range_percent:+.2f}%"
            )

        # Create simple line chart for gold prices
        st.subheader("Gold Price History")

        # Convert to simple data structures for plotting
        dates = gold_df['Date'].tolist()
        closes = gold_df['Close'].tolist()

        # Create a price chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(dates, closes, 'b-')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price (USD)')
        ax.set_title('Gold Price History')
        ax.grid(True, alpha=0.3)

        # Display chart
        st.pyplot(fig)

        # Create a more detailed view with table
        st.subheader("Recent Price Data")

        # Show data table with recent values
        recent_data = gold_df.tail(30).copy()

        # Format date column
        if 'Date' in recent_data.columns:
            recent_data['Date'] = recent_data['Date'].dt.strftime('%Y-%m-%d')

        # Display as a table
        st.dataframe(recent_data[['Date', 'Open', 'High', 'Low',
                     'Close', 'Volume']], use_container_width=True)

        # Additional analysis data is available
        with st.expander("View Complete Dataset"):
            st.dataframe(gold_df, use_container_width=True)

    except Exception as e:
        st.error(
            f"Error processing gold price data: {type(e).__name__} - {str(e)}")
        st.exception(e)
