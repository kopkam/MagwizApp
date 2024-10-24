import streamlit as st
import sqlite3
import pandas as pd
import io
import plotly.graph_objects as go
import plotly.express as px

# Function to establish a connection to the database
def connect_db():
    conn = sqlite3.connect('db_inventory.db')
    return conn

# Function to load data from the database
def load_data(conn):
    query = """
        SELECT DATE(sm.data_state) AS 'State Date',
               p.product_name AS 'Product Name',
               sm.available_quantity AS 'Available Quantity',
               p.safety_stock AS 'Safety Stock'
        FROM InventoryStates sm
        JOIN Products p ON sm.product_code = p.product_code
        WHERE sm.available_quantity < p.safety_stock
        ORDER BY sm.data_state, p.product_name
    """
    df = pd.read_sql_query(query, conn)
    return df

# Function to generate the bar chart
def generate_plot(df, selected_dates, search_term):
    fig = go.Figure()
    
    # Define a color palette for the bars
    colors = px.colors.qualitative.Plotly
    
    # Sort selected dates in ascending order
    selected_dates.sort()

    for i, date in enumerate(selected_dates):
        filtered_df = df[df['State Date'] == date]

        if search_term:
            filtered_df = filtered_df[filtered_df['Product Name'].str.contains(search_term, case=False)]

        shortages = abs(filtered_df['Available Quantity'] - filtered_df['Safety Stock']).sum()

        fig.add_trace(go.Bar(
            name=f'{date}',
            x=['Available Quantity', 'Minimum Quantity'],
            y=[filtered_df['Available Quantity'].sum(), shortages],
            marker_color=colors[i % len(colors)]  # Use modulo to cycle through colors if more dates than colors
        ))

    fig.update_layout(title='Product Availability and Minimum Stock Levels', barmode='group')
    return fig

# Function to display the data and chart
def main():
    st.title('Display Products Requiring Restock')

    conn = connect_db()
    df = load_data(conn)
    conn.close()

    latest_date = df['State Date'].max()

    selected_dates = st.multiselect('Select dates to filter:', df['State Date'].unique(), default=[latest_date])
    
    # If no date is selected, use the most recent available date
    if not selected_dates:
        selected_dates = [latest_date]

    search_term = st.text_input("Enter product name to filter:")

    # Add a "Stock Difference" column
    df['Missing Quantity'] = df['Safety Stock'] - df['Available Quantity']

    # Display the filtered data table
    filtered_df = df[df['State Date'].isin(selected_dates)]
    if search_term:
        filtered_df = filtered_df[filtered_df['Product Name'].str.contains(search_term, case=False)]
    st.dataframe(filtered_df.drop(columns=['State Date']), hide_index=True)

    # Add button to download the data as an Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    st.download_button(
        label="Download as Excel file",
        data=output.getvalue(),
        file_name="inventory_shortages.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown('---')

    # Display warehouse shortages for each selected date
    for date in selected_dates:
        # Filter data for the specific date
        filtered_date_df = filtered_df[filtered_df['State Date'] == date]

        # Calculate shortages for the selected date
        shortages_date = abs(filtered_date_df['Available Quantity'] - filtered_date_df['Safety Stock']).sum()

        # Display the shortage count as a metric in the Streamlit app
        st.metric(label=f"Warehouse shortages for {date}", value=int(shortages_date))

    st.markdown('---')
    # Generate the bar chart
    fig = generate_plot(df, selected_dates, search_term)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
