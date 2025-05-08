import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_BASE_URL = "https://bnwuaviahfwgqpakswwj.supabase.co"
TABLE_NAME = "payments"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_BASE_URL, SUPABASE_API_KEY)

# Function to save data to Supabase
def save_to_supabase(df, supabase_client, table_name):
    df["payment_date"] = pd.to_datetime(df["payment_date"]).dt.strftime('%Y-%m-%d')
    rows = df.to_dict(orient="records")
    errors = []
    for row in rows:
        response = supabase_client.table(table_name).insert(row).execute()
        if response is None:
            errors.append(row)

    if errors:
        st.error(f"Failed to upload {len(errors)} rows. Check the data and try again.")
        st.write(response)
    else:
        st.success(f"Successfully uploaded {len(rows)} rows to Supabase!")

def main():
    st.set_page_config(
        page_title="Accounting Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    APP_PASSWORD = os.getenv("PASSWORD")
    
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if not st.session_state['authenticated']:
        password_input = st.text_input("🔒 Enter Password to Unlock", type="password")
        if password_input == APP_PASSWORD:
            st.session_state['authenticated'] = True
            st.success("✅ Access granted! Welcome to the Accounting Dashboard.")
        else:
            st.warning("Please enter the correct password to continue.")
            st.stop()
            
    st.title("📊 **Accounting Dashboard**")
    st.markdown("### Gain Insights Into Your Payments")

    with st.sidebar:
        st.image("https://www.ustayinusa.com/logo.svg")
        st.markdown("### **Accounting Summary**")
        st.write("Explore accounting statistics and submit payment to register.")

    if "mode" not in st.session_state:
        st.session_state["mode"] = "View"

    def activate_view():
        st.session_state["mode"] = "View"

    def activate_edit():
        st.session_state["mode"] = "Edit"

    left, right = st.columns(2)
    left.button("🔍 View Mode", on_click=activate_view, use_container_width=True)
    right.button("✏️ Edit Mode", on_click=activate_edit, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state["mode"] == "View":
        months = ["Whole Year", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        years = [2024, 2025]

        col1, col2 = st.columns(2)
        with col1:
            year_selected = st.radio("📅 Select the Year", years)
        with col2:
            month_selected = st.selectbox("📅 Select the Month", months)

        st.markdown("## **Filtered Payments Overview**")
        st.markdown("---")

        with st.spinner("Fetching data..."):
            if month_selected == "Whole Year":
                response = supabase.table(TABLE_NAME).select("*") \
                    .filter("payment_date", "gte", f"{year_selected}-01-01") \
                    .filter("payment_date", "lt", f"{year_selected + 1}-01-01") \
                    .execute()
            else:
                month_index = months.index(month_selected)
                if month_index == 12:
                    start_date = f"{year_selected}-12-01"
                    end_date = f"{year_selected + 1}-01-01"
                else:
                    start_date = f"{year_selected}-{month_index:02d}-01"
                    end_date = f"{year_selected}-{month_index + 1:02d}-01"

                response = supabase.table(TABLE_NAME).select("*") \
                    .filter("payment_date", "gte", start_date) \
                    .filter("payment_date", "lt", end_date) \
                    .execute()

            # Initialize safe defaults
            total_cost = 0
            max_cost_per_category = pd.Series(dtype='float64')
            most_frequent_category = "None"
            average_payment = 0
            total_payments = 0
            expenses_over_time = pd.Series(dtype='float64')
            top_payments = pd.DataFrame(columns=["payment_date", "payment_description", "payment_value"])

            try:
                if response and response.data:
                    df = pd.DataFrame(response.data)
                    if not df.empty and "payment_date" in df.columns:
                        df["payment_date"] = pd.to_datetime(df["payment_date"])

                        total_cost = df["payment_value"].sum()
                        max_cost_per_category = df.groupby('payment_category')["payment_value"].sum()
                        most_frequent_category = df["payment_category"].mode()[0] if not df["payment_category"].mode().empty else "None"
                        average_payment = df["payment_value"].mean()
                        total_payments = df.shape[0]

                        expenses_over_time = df.groupby("payment_date")["payment_value"].sum()
                        top_payments = df.nlargest(5, "payment_value")
            except Exception as e:
                st.warning(f"⚠️ Data processing skipped due to: {e}")

            if total_payments > 0:
                max_category_name = max_cost_per_category.idxmax() if not max_cost_per_category.empty else "None"
                max_category_value = max_cost_per_category.max() if not max_cost_per_category.empty else 0
                top_cost_percentage = (max_category_value / total_cost) * 100 if total_cost > 0 else 0
            else:
                max_category_name = "None"
                max_category_value = 0
                top_cost_percentage = 0

            st.subheader("💡 Key Metrics")
            col1, col2, col3 = st.columns(3)
            col1.metric(f"💵 Total Cost ({month_selected} {year_selected})", f"${total_cost:,.2f}")
            col2.metric("🏷️ Top Cost Category", f"{max_category_name} (${max_category_value:,.2f})")
            col3.metric("📊 Top Cost %", f"{top_cost_percentage:.2f}%")

            col4, col5, col6 = st.columns(3)
            col4.metric("💰 Average Payment", f"${average_payment:,.2f}")
            col5.metric("📄 Total Payments", total_payments)
            col6.metric("🛠️ Most Frequent Category", most_frequent_category)

            st.markdown("<hr>", unsafe_allow_html=True)

            st.subheader("📈 **Visual Analytics**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Expenses Over Time**")
                st.line_chart(expenses_over_time)

            with col2:
                st.markdown("**Cost Distribution by Category**")
                st.bar_chart(max_cost_per_category)

            st.markdown("<hr>", unsafe_allow_html=True)

            st.subheader("🏆 Top 5 Highest Payments")
            st.table(top_payments)

    elif st.session_state["mode"] == "Edit":
        st.markdown("## ✏️ **Edit Mode: Add or Upload Payments**")
        st.markdown("---")

        st.subheader("📝 **Manual Input**")
        with st.form("Input Payment"):
            categories = ["Employee", "Profit Withdraw", "Softwares", "Operating Costs", "Inbound Development", "Marketing", "Taxes", "Outbound Development", "Other"]
            agents = ["Joao Santos", "Rafael Garcia", "Lucas Lobo"]
            payment_value = st.number_input("💵 Input Value in USD", min_value=0.0, step=0.01, format="%.2f")
            payment_category = st.selectbox("🏷️ Categories", options=categories)
            payment_date = st.date_input("📅 When was the payment done?")
            payment_agent = st.selectbox("🛠️ Agent", agents)
            payment_description = st.text_area("📜 Payment Description")
            submit_button = st.form_submit_button("Submit Payment")
            if submit_button:
                new_payment = {
                    "payment_value": payment_value,
                    "payment_category": payment_category,
                    "payment_date": payment_date.isoformat(),
                    "payment_agent": payment_agent,
                    "payment_description": payment_description.strip(),
                }
                response = supabase.table(TABLE_NAME).insert(new_payment).execute()
                if response.data is not None:
                    st.toast("✅ Payment submitted successfully!", icon='🎉')
                else:
                    st.error(f"❌ Failed to submit payment")

        st.subheader("📂 **Upload Prepared CSV**")
        uploaded_file = st.file_uploader("Choose a prepared CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                df_prepared = pd.read_csv(uploaded_file)
                st.write("📝 **Preview of Uploaded Data:**", df_prepared.head())

                if st.button("📤 Upload to Supabase"):
                    with st.spinner("Uploading data to Supabase..."):
                        save_to_supabase(df_prepared, supabase, TABLE_NAME)
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")

        expander = st.expander("Check Last Payment")
        last_payment = supabase.table(TABLE_NAME) \
            .select("*") \
            .order("id", desc=True) \
            .limit(1) \
            .execute()
        
        data = last_payment.data

        if data: 
            last_row = data[0] 

            payment_id = last_row.get("id")
            created_at = last_row.get("created_at")
            payment_value = last_row.get("payment_value")
            payment_category = last_row.get("payment_category")
            payment_date = last_row.get("payment_date")
            payment_agent = last_row.get("payment_agent")
            payment_description = last_row.get("payment_description")

            expander.write(f'''
                Payment ID: {payment_id} \n
                Created At: {created_at} \n
                Payment Value: {payment_value} \n
                Payment Category: {payment_category} \n
                Payment Date: {payment_date} \n
                Payment Agent: {payment_agent} \n
                Payment Description: {payment_description} \n
            ''')
        else:
            expander.write("No data found.")

if __name__ == "__main__":
    main()