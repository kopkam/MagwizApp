import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

# Function to load data
def load_data(option):
    # Connection to SQLite3 database
    conn = sqlite3.connect('db_inventory.db')

    if option == "Delivery Lead Time":
        # SQL query for supplier data
        query = """
        SELECT 
            DS.id_delivery AS 'Delivery Number',
            S.supplier_name AS 'Supplier Name', 
            DATE(DS.order_date) AS 'Order Date', 
            DATE(DS.delivery_date) AS 'Delivery Date', 
            (julianday(DS.delivery_date) - julianday(DS.order_date)) AS 'Lead Time (days)'
        FROM Deliveries DS
        JOIN Suppliers S ON DS.id_supplier = S.id_supplier;
        """
    elif option == "Shipping Lead Time":
        # SQL query for customer data
        query = """
        SELECT 
            O.id_order AS 'Order Number',
            C.customer_name AS 'Customer Name', 
            DATE(O.order_date) AS 'Order Date', 
            DATE(O.shipping_date) AS 'Shipping Date', 
            (julianday(O.shipping_date) - julianday(O.order_date)) AS 'Lead Time (days)'
        FROM Orders O
        JOIN Customers C ON O.id_customer = C.id_customer;
        """

    # Execute the query and load results into a DataFrame
    df = pd.read_sql_query(query, conn)

    # Close the connection to the database
    conn.close()

    return df

# Load data based on user's selection
option = st.sidebar.radio("Select data to display", ("Delivery Lead Time", "Shipping Lead Time"))
df = load_data(option)

# Display title
st.title('Order Lead Time Indicator')

# Display data for suppliers
if option == "Delivery Lead Time":
    st.subheader("Delivery Lead Time")
        
    # Convert date to datetime
    df['Order Date'] = pd.to_datetime(df['Order Date']).dt.date

    # Interactive date range slider
    min_date = min(df['Order Date'])
    max_date = max(df['Order Date'])
    start_date = st.date_input("Select start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Select end date", min_value=min_date, max_value=max_date, value=max_date)

    # Convert date to datetime object
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Validate date range
    if start_date > end_date:
        st.error("Error: Start date cannot be later than end date!")
    elif start_date == end_date:
        st.error("Error: Start and end dates cannot be the same!")
    else:
        # Filter data based on the selected date range
        filtered_df = df[(df['Order Date'] >= start_date.date()) & (df['Order Date'] <= end_date.date())]
        
        # Display filtered data
        st.dataframe(filtered_df, hide_index=True)

        # Calculate cycle lead time
        filtered_df['Cycle Lead Time'] = (pd.to_datetime(filtered_df['Delivery Date']) - pd.to_datetime(filtered_df['Order Date'])).dt.days

        # Add Excel download button
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Download as Excel file",
            data=output.getvalue(),
            file_name="delivery_lead_time.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown('---')

        # Calculate average lead time
        average_cycle_time = filtered_df['Cycle Lead Time'].mean()
        # Average lead time in hours
        average_cycle_time_hours = average_cycle_time * 24
        st.subheader(f"Average delivery lead time from {start_date.date()} to {end_date.date()}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric('', f"{average_cycle_time:.2f} (days)", label_visibility='visible')
        with col2:
            st.metric('', f"{average_cycle_time_hours:.2f} (hours)", label_visibility='visible')
        st.markdown('---')
    
    # Calculate average delivery time for each supplier
    average_delivery_time = filtered_df.groupby('Supplier Name')['Cycle Lead Time'].mean().reset_index()
    # Find the supplier with the longest average lead time
    slowest_supplier = average_delivery_time.loc[average_delivery_time['Cycle Lead Time'].idxmax()]
    # Prepare info about the slowest supplier in HTML format
    slowest_supplier_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Slowest Supplier</h3><p>{slowest_supplier['Supplier Name']}</p></div><div style='text-align: center;'><h3>Average Lead Time (days)</h3><p>{slowest_supplier['Cycle Lead Time']:.2f}</p></div></div>"
    # Find the supplier with the shortest average lead time
    fastest_supplier = average_delivery_time.loc[average_delivery_time['Cycle Lead Time'].idxmin()]
    fastest_supplier_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Fastest Supplier</h3><p>{fastest_supplier['Supplier Name']}</p></div><div style='text-align: center;'><h3>Average Lead Time (days)</h3><p>{fastest_supplier['Cycle Lead Time']:.2f}</p></div></div>"
    st.markdown(fastest_supplier_info, unsafe_allow_html=True)
    # Display info about the slowest supplier
    st.markdown(slowest_supplier_info, unsafe_allow_html=True)

# Display data for customers
elif option == "Shipping Lead Time":
    st.subheader("Shipping Lead Time")

    # Convert date to datetime
    df['Order Date'] = pd.to_datetime(df['Order Date']).dt.date

    # Interactive date range slider
    min_date = min(df['Order Date'])
    max_date = max(df['Order Date'])
    start_date = st.date_input("Select start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Select end date", min_value=min_date, max_value=max_date, value=max_date)

    # Convert date to datetime object
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Validate date range
    if start_date > end_date:
        st.error("Error: Start date cannot be later than end date!")
    elif start_date == end_date:
        st.error("Error: Start and end dates cannot be the same!")
    else:
        # Filter data based on the selected date range
        filtered_df = df[(df['Order Date'] >= start_date.date()) & (df['Order Date'] <= end_date.date())]
        
        # Display filtered data
        st.dataframe(filtered_df, hide_index=True)

        # Calculate cycle lead time
        filtered_df['Cycle Lead Time'] = (pd.to_datetime(filtered_df['Shipping Date']) - pd.to_datetime(filtered_df['Order Date'])).dt.days

        # Add Excel download button
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Download as Excel file",
            data=output.getvalue(),
            file_name="shipping_lead_time.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown('---')

        # Calculate average lead time
        average_cycle_time = filtered_df['Cycle Lead Time'].mean()
        # Average lead time in hours
        average_cycle_time_hours = average_cycle_time * 24
        st.subheader(f"Average shipping lead time from {start_date.date()} to {end_date.date()}")
        col1, col2 = st.columns(2)

        with col1:
            st.metric('', f"{average_cycle_time:.2f} (days)", label_visibility='visible')
        with col2:
            st.metric('', f"{average_cycle_time_hours:.2f} (hours)", label_visibility='visible')

    st.markdown('---')

    # Calculate average shipping time for each customer
    average_delivery_time = filtered_df.groupby('Customer Name')['Cycle Lead Time'].mean().reset_index()
    slowest_customer = average_delivery_time.loc[average_delivery_time['Cycle Lead Time'].idxmax()]
    slowest_customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Slowest Customer</h3><p>{slowest_customer['Customer Name']}</p></div><div style='text-align: center;'><h3>Average Shipping Lead Time (days)</h3><p>{slowest_customer['Cycle Lead Time']:.2f}</p></div></div>"
    fastest_customer = average_delivery_time.loc[average_delivery_time['Cycle Lead Time'].idxmin()]
    fastest_customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Fastest Customer</h3><p>{fastest_customer['Customer Name']}</p></div><div style='text-align: center;'><h3>Average Shipping Lead Time (days)</h3><p>{fastest_customer['Cycle Lead Time']:.2f}</p></div></div>"
    st.markdown(fastest_customer_info, unsafe_allow_html=True)
    st.markdown(slowest_customer_info, unsafe_allow_html=True)