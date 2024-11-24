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

    if option == "Delivery Timeliness":
        # SQL query for suppliers
        query = """
        SELECT 
            DS.delivery_id AS 'Delivery Number',
            S.supplier_name AS 'Supplier Name', 
            DATE(DS.order_date) AS 'Order Date', 
            DATE(DS.expected_delivery_date)  AS 'Expected Delivery Date', 
            DATE(DS.delivery_date) AS 'Delivery Date', 
            DS.delivery_status AS 'Delivery Status'
        FROM Deliveries DS
        JOIN Suppliers S ON DS.supplier_id = S.supplier_id;
        """
    elif option == "Shipping Timeliness":
        # SQL query for customers
        query = """
        SELECT 
            O.order_id AS 'Order Number',
            C.customer_name AS 'Customer Name', 
            DATE(O.order_date) AS 'Order Date', 
            DATE(O.expected_shipping_date) AS 'Expected Shipping Date', 
            DATE(O.shipping_date) AS 'Shipping Date', 
            O.shipping_status AS 'Shipping Status'
        FROM Orders O
        JOIN Customers C ON O.customer_id = C.customer_id;
        """

    # Execute the query and load results into a DataFrame
    df = pd.read_sql_query(query, conn)
    # Close the connection to the database
    conn.close()
    # Return the DataFrame
    return df

# Load data
option = st.sidebar.radio("Select data to display", ("Delivery Timeliness", "Shipping Timeliness"))
df = load_data(option)

# Display title
st.title('Order Timeliness Indicator')

# Function to display data for suppliers
def display_supplier_data(df):

    st.subheader("Supplier Delivery Timeliness")

    # Select values to display in the chart
    selected_values = st.multiselect("Select delivery status", df['Delivery Status'].unique(), default=[])

    # Convert date to datetime
    df['Order Date'] = pd.to_datetime(df['Order Date']).dt.date

    # Add interactive date slider
    min_date = min(df['Order Date'])
    max_date = max(df['Order Date'])

    # Safeguard: the minimum date cannot be greater than the maximum date
    start_date = st.date_input("Select start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Select end date", min_value=min_date, max_value=max_date, value=max_date)

    # Convert the date to a datetime object
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Check if selected dates are valid
    if start_date > end_date:
        st.error("Error: The start date cannot be greater than the end date!")
    elif start_date == end_date:
        st.error("Error: The start and end dates cannot be the same!")
    else:
        # Filter data based on the selected time period
        filtered_df = df[(df['Order Date'] >= start_date.date()) & (df['Order Date'] <= end_date.date())]

        # Check if any filter has been selected
        if selected_values:
            # Display the DataFrame only when a filter is selected
            st.dataframe(filtered_df[filtered_df['Delivery Status'].isin(selected_values)], hide_index=True)
        else:
            # Display the full DataFrame when no filters are selected
            st.dataframe((filtered_df), hide_index=True)

        # Add button to download data as Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Download as Excel",
            data=output.getvalue(),
            file_name="supplier_timeliness.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Add a dividing line
        st.markdown("---")
        
# Creating charts for selected values
    selected_value = 'Completed on time'  # The selected value will always be 'On Time'

    # Filter data for the selected value
    filtered_status_df = filtered_df[filtered_df['Delivery Status'] == selected_value]

    # Calculate the percentage of the selected value occurrence
    percent_value = (filtered_df['Delivery Status'] == selected_value).mean() * 100

    # Set colors for thresholds
    value = percent_value
    colors = ["red", "orange", "green"]
    thresholds = [0, 50, 75, 100]

    # Function to find the color based on the value
    def find_color(val, thresholds, colors):
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= val < thresholds[i + 1]:
                return colors[i]
        return colors[-1]

    # Find the color for the value
    bar_color = find_color(value, thresholds, colors)
    value_color = find_color(value, thresholds, colors)

    # Create an interactive gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickfont': {'color': 'black'}, 'tickvals': list(range(0, 101, 10))}, 
            'bgcolor': 'white',
            'bar': {'color': bar_color},
            'borderwidth': 2,
            'bordercolor': "gray",
            'threshold': {
                'line': {'color': "black", 'width': 11},
                'thickness': 0.9,
                'value': value}
        }
    ))

    # Update layout
    fig.update_layout(font={'color': "white", 'family': "Arial"})

    # Update value color
    fig.update_traces(number_font_color=value_color)

    # Display the chart with background
    st.write(f"## Percentage of deliveries made on time from {start_date.date()} to {end_date.date()}")
    st.plotly_chart(fig)

    # Add a dividing line
    st.markdown("---")

    # Default selection: 'On Time' and 'Late'
    selected_values = ['Completed on time', 'Completed with a delay']

    if not selected_values:
        selected_values = ['Completed on time', 'Completed with a delay']
    
    # Check selected values in the select box
    for selected_value in selected_values:
        # Filter data for the selected delivery status
        if selected_value == 'Completed on time':
            filtered_status_df = df[df['Delivery Status'] == 'Completed on time']
            supplier_label = "Best Supplier"
            record_label = "Number of On-Time Deliveries"
        elif selected_value == 'Completed with a delay':
            filtered_status_df = df[df['Delivery Status'] == 'Completed with a delay']
            supplier_label = "Worst Supplier"
            record_label = "Number of Late Deliveries"

        # Filter data based on selected dates
        filtered_status_df = filtered_status_df[(filtered_status_df['Order Date'] >= start_date.date()) & (filtered_status_df['Order Date'] <= end_date.date())]

        # Group data by supplier name and count the records
        count_by_supplier = filtered_status_df.groupby('Supplier Name').size().reset_index(name='Record Count')

        # Find the record with the highest or lowest number of records
        if selected_value == 'Completed on time':
            max_record = count_by_supplier.loc[count_by_supplier['Record Count'].idxmax()]
        elif selected_value == 'Completed with a delay':
            max_record = count_by_supplier.loc[count_by_supplier['Record Count'].idxmax()]

        # Creating information about the supplier in a similar style
        supplier_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>{supplier_label}</h3><p>{max_record['Supplier Name']}</p></div><div style='text-align: center; margin: auto;'><h3>{record_label}</h3><p>{max_record['Record Count']}</p></div></div>"

        st.markdown(supplier_info, unsafe_allow_html=True)

# Function to display data for customers
def display_customer_data(df):

    st.subheader("Customer Shipping Timeliness")

    # Select values to display in the chart
    selected_values = st.multiselect("Select shipping status", df['Shipping Status'].unique(), default=[])

    # Convert date to datetime
    df['Order Date'] = pd.to_datetime(df['Order Date']).dt.date

    # Add interactive date slider
    min_date = min(df['Order Date'])
    max_date = max(df['Order Date'])

    # Safeguard: the minimum date cannot be greater than the maximum date
    start_date = st.date_input("Select start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Select end date", min_value=min_date, max_value=max_date, value=max_date)

    # Convert the date to a datetime object
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Check if selected dates are valid
    if start_date > end_date:
        st.error("Error: The start date cannot be greater than the end date!")
    elif start_date == end_date:
        st.error("Error: The start and end dates cannot be the same!")
    else:
        # Filter data based on the selected time period
        filtered_df = df[(df['Order Date'] >= start_date.date()) & (df['Order Date'] <= end_date.date())]

        # Check if any filter has been selected
        if selected_values:
            # Display the DataFrame only when a filter is selected
            st.dataframe(filtered_df[filtered_df['Shipping Status'].isin(selected_values)], hide_index=True)
        else:
            # Display the full DataFrame when no filters are selected
            st.dataframe((filtered_df), hide_index=True)

        # Add button to download data as Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Download as Excel",
            data=output.getvalue(),
            file_name="customer_timeliness.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Add a dividing line
        st.markdown("---")

    # Creating charts for selected values
    selected_value = 'Completed on time'  # The selected value will always be 'Delivered on time'

    # Filtering data for the selected value
    filtered_status_df = filtered_df[filtered_df['Shipping Status'] == selected_value]

    # Calculating the percentage occurrence of the selected value
    percent_value = (filtered_df['Shipping Status'] == selected_value).mean() * 100

    # Defining colors for thresholds
    value = percent_value
    colors = ["red", "orange", "green"]
    thresholds = [0, 50, 75, 100]



    # Function to find the color based on the value
    def find_color(val, thresholds, colors):
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= val < thresholds[i + 1]:
                return colors[i]
        return colors[-1]

    # Finding the color for the value
    bar_color = find_color(value, thresholds, colors)
    value_color = find_color(value, thresholds, colors)

    # Creating an interactive gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100], 'tickfont': {'color': 'black'}, 'tickvals': list(range(0, 101, 10))}, 
            'bgcolor': 'white',
            'bar': {'color': bar_color},
            'borderwidth': 2,
            'bordercolor': "gray",
            'threshold': {
                'line': {'color': "black", 'width': 11},
                'thickness': 0.9,
                'value': value}
        }
    ))

    # Updating layout
    fig.update_layout(font={'color': "white", 'family': "Arial"})

    # Retrieving background color via CSS
    # Updating value color
    fig.update_traces(number_font_color=value_color)

    # Displaying the chart with background
    st.write(f"## Percentage of on-time deliveries in the period from {start_date.date()} to {end_date.date()}")
    st.plotly_chart(fig)

    # Adding a separator line
    st.markdown("---")

    # Default selected statuses: 'Delivered on time' and 'Delivered late'
    if not selected_values:
        selected_values = ['Completed on time', 'Completed with a delay']  # If nothing is selected, select both statuses

    for selected_value in selected_values:
        # Filtering data for the selected shipping status
        if selected_value == 'Completed on time':
            filtered_status_df = df[df['Shipping Status'] == 'Completed on time']
            customer_label = "Best served customer"
            record_label = "Number of on-time deliveries"
        elif selected_value == 'Completed with a delay':
            filtered_status_df = df[df['Shipping Status'] == 'Completed with a delay']
            customer_label = "Worst served customer"
            record_label = "Number of delayed deliveries"
        else:
            filtered_status_df = df[df['Shipping Status'] == 'Completed with a delay']
            customer_label = "Worst served customer"
            record_label = "Number of delayed deliveries"

        # Filtering data by selected dates
        filtered_status_df = filtered_status_df[(filtered_status_df['Order Date'] >= start_date.date()) & (filtered_status_df['Order Date'] <= end_date.date())]

        # Grouping data by customer name and counting records
        count_by_customer = filtered_status_df.groupby('Customer Name').size().reset_index(name='Record Count')

        # Finding the record with the highest or lowest count
        if selected_value == 'Completed on time':
            max_record = count_by_customer.loc[count_by_customer['Record Count'].idxmax()]
        elif selected_value == 'Completed with a delay':
            max_record = count_by_customer.loc[count_by_customer['Record Count'].idxmax()]

        # Creating customer info in a similar style
        customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>{customer_label}</h3><p>{max_record['Customer Name']}</p></div><div style='text-align: center;'><h3>{record_label}</h3><p>{max_record['Record Count']}</p></div></div>"
        st.markdown(customer_info, unsafe_allow_html=True)

# Select which option to display
if option == "Delivery Timeliness":
    display_supplier_data(df)
elif option == "Shipping Timeliness":
    display_customer_data(df)