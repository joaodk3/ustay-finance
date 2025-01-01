import streamlit as st
import pandas as pd
from backend.api.monday import df_sales
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_BASE_URL = "https://bnwuaviahfwgqpakswwj.supabase.co"
TABLE_NAME = "payments"

# Set pandas option globally to suppress warnings
pd.set_option('future.no_silent_downcasting', True)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_BASE_URL, SUPABASE_API_KEY)

def main():
    st.set_page_config(
        page_title="Finance Dashboard",
        page_icon="📊",
        layout="wide"
    )
    st.title("📊 **Finance Dashboard**")
    st.markdown("### Compare Revenue and Costs with Detailed Insights")

    # Year and Month selection
    months = ["Whole Year", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    years = [2024, 2025]

    col1, col2 = st.columns(2)
    with col1:
        year_selected = st.radio("📅 Select the Year", years)
    with col2:
        month_selected = st.selectbox("📅 Select the Month", months)

    with st.sidebar:
        st.image("https://www.ustayinusa.com/logo.svg")
        st.markdown("### **Finance Summary**")
        st.write("Explore your finances with detailed comparisons between revenue and costs.")

    # Ensure "Pmt Date" is in datetime format
    df_sales["Pmt Date"] = pd.to_datetime(df_sales["Pmt Date"], format="%Y-%m-%d", errors="coerce")

    # Filter DataFrame based on selected year and month
    if month_selected == "Whole Year":
        filtered_df = df_sales[df_sales["Pmt Date"].dt.year == year_selected]
        previous_period_df = df_sales[df_sales["Pmt Date"].dt.year == year_selected - 1]
    else:
        month_index = months.index(month_selected)
        filtered_df = df_sales[
            (df_sales["Pmt Date"].dt.year == year_selected) & (df_sales["Pmt Date"].dt.month == month_index)
        ]
        previous_period_df = df_sales[
            (df_sales["Pmt Date"].dt.year == (year_selected if month_index > 1 else year_selected - 1)) &
            (df_sales["Pmt Date"].dt.month == (month_index - 1 if month_index > 1 else 12))
        ]

    # Convert "Total Amount" to numeric
    filtered_df.loc[:, "Total Amount"] = pd.to_numeric(filtered_df["Total Amount"], errors="coerce")
    previous_period_df.loc[:, "Total Amount"] = pd.to_numeric(previous_period_df["Total Amount"], errors="coerce")

    # Fetch costs data from Supabase
    with st.spinner("Fetching cost data..."):
        if month_selected == "Whole Year":
            start_date, end_date = f"{year_selected}-01-01", f"{year_selected + 1}-01-01"
            prev_start_date, prev_end_date = f"{year_selected - 1}-01-01", f"{year_selected}-01-01"
        else:
            start_date = f"{year_selected}-{month_index:02d}-01"
            end_date = f"{year_selected}-{month_index + 1:02d}-01" if month_index < 12 else f"{year_selected + 1}-01-01"
            prev_start_date = f"{year_selected}-{month_index - 1:02d}-01" if month_index > 1 else f"{year_selected - 1}-12-01"
            prev_end_date = start_date

        response = supabase.table(TABLE_NAME).select("*") \
            .filter("payment_date", "gte", start_date) \
            .filter("payment_date", "lt", end_date) \
            .execute()
        prev_response = supabase.table(TABLE_NAME).select("*") \
            .filter("payment_date", "gte", prev_start_date) \
            .filter("payment_date", "lt", prev_end_date) \
            .execute()

    # Prepare cost DataFrame
    df = pd.DataFrame(response.data or [])
    prev_df = pd.DataFrame(prev_response.data or [])

    # Metrics Calculation
    revenue = filtered_df["Total Amount"].sum() if not filtered_df.empty else 0
    cost = df["payment_value"].sum() if not df.empty else 0
    profit = revenue - cost

    previous_revenue = previous_period_df["Total Amount"].sum() if not previous_period_df.empty else 0
    previous_cost = prev_df["payment_value"].sum() if not prev_df.empty else 0

    # Calculate deltas
    revenue_delta = f"{((revenue - previous_revenue) / previous_revenue * 100):.2f}%" if previous_revenue > 0 else "N/A"
    cost_delta = f"{((cost - previous_cost) / previous_cost * 100):.2f}%" if previous_cost > 0 else "N/A"
    profit_margin = (profit / revenue * 100) if revenue > 0 else 0

    # Handle duplicates in time_series and time_series_cost
    time_series = filtered_df.set_index("Pmt Date")["Total Amount"].groupby("Pmt Date").sum()
    time_series_cost = df.groupby("payment_date")["payment_value"].sum()

    # Combine data with explicit infer_objects()
    combined = pd.concat([time_series.rename("Revenue"), time_series_cost.rename("Costs")], axis=1).fillna(0).infer_objects()

    # Display Metrics
    st.markdown("## **Key Metrics**")
    col3, col4, col5 = st.columns(3)
    col3.metric("💵 Revenue", f"${revenue:,.2f}", revenue_delta)
    col4.metric("📉 Costs", f"${cost:,.2f}", cost_delta)
    col5.metric("💰 Profit", f"${profit:,.2f}")

    col6, col7 = st.columns(2)
    col6.metric("📊 Profit Margin", f"{profit_margin:.2f}%")
    col7.metric("📉 Cost Margin", f"{(cost / revenue * 100) if revenue > 0 else 0:.2f}%")

    st.markdown("---")

    # Visualizations
    st.markdown("## **Visual Analytics**")
    col8, col9 = st.columns(2)
    with col8:
        st.markdown("### Revenue vs. Costs Over Time")
        st.line_chart(combined)

    with col9:
        st.markdown("### Cost Distribution by Category")
        cost_distribution = df.groupby("payment_category")["payment_value"].sum()
        st.bar_chart(cost_distribution)

    st.markdown("---")


if __name__ == "__main__":
    main()