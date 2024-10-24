import sqlite3
import pandas as pd
import streamlit as st
import io
import plotly.express as px

def connect_db():
    return sqlite3.connect('db_inventory.db')

def get_data(selected_dates, selected_magazines, product_name):
    conn = connect_db()
    dates_filter = "'" + "', '".join(selected_dates) + "'"
    magazines_filter = "'" + "', '".join(selected_magazines) + "'" if selected_magazines else "ALL"
    where_clause = f"DATE(s.data_state) IN ({dates_filter})"
    if selected_magazines:
        where_clause += f" AND m.warehouse_name IN ({magazines_filter})"
    if product_name:
        where_clause += f" AND p.product_name LIKE '%{product_name}%'"
    query = f"""
    SELECT 
        DATE(s.data_state) AS Data_State,
        p.product_name AS Product_Name,
        m.warehouse_name AS Warehouse_Name,
        s.available_quantity AS Available_Quantity
    FROM 
        InventoryStates s
    JOIN 
        Products p ON s.product_code = p.product_code
    JOIN 
        Warehouses m ON s.id_warehouse = m.id_warehouse
    WHERE 
        {where_clause};
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_chart_data(selected_dates, selected_magazines):
    conn = connect_db()
    dates_filter = "'" + "', '".join(selected_dates) + "'"
    magazines_filter = "'" + "', '".join(selected_magazines) + "'" if selected_magazines else "ALL"
    where_clause = f"DATE(s.data_state) IN ({dates_filter})"
    if selected_magazines:
        where_clause += f" AND m.warehouse_name IN ({magazines_filter})"
    query = f"""
    SELECT 
        DATE(s.data_state) AS Data_State,
        m.warehouse_name AS Warehouse_Name,
        SUM(s.available_quantity) AS Available_Quantity
    FROM 
        InventoryStates s
    JOIN 
        Warehouses m ON s.id_warehouse = m.id_warehouse
    WHERE 
        {where_clause}
    GROUP BY 
        DATE(s.data_state), m.warehouse_name;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    conn = connect_db()
    dates_query = "SELECT DISTINCT DATE(data_state) AS data_state FROM InventoryStates ORDER BY data_state ASC;"
    dates = pd.read_sql_query(dates_query, conn)['data_state'].tolist()
    magazines_query = "SELECT DISTINCT warehouse_name FROM Warehouses;"
    magazines = pd.read_sql_query(magazines_query, conn)['warehouse_name'].tolist()
    conn.close()
    latest_date = max(dates) if dates else None

    st.write("# Inventory Status on Selected Date")
    selected_dates = st.multiselect("Select dates:", dates, default=[latest_date] if latest_date else [])
    selected_magazines = st.multiselect("Select warehouses:", magazines)
    product_name = st.text_input("Enter product name to filter:")
    if not selected_dates and latest_date:
        selected_dates = [latest_date]
    df = get_data(selected_dates, selected_magazines, product_name)
    df = df.rename(columns={"Data_State": "Date of State", "Product_Name": "Product Name", "Warehouse_Name": "Warehouse Name", "Available_Quantity": "Available Quantity"})
    st.dataframe(df, hide_index=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
         df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    st.download_button(
          label="Download as Excel file",
          data=output.getvalue(),
          file_name="inventory_status.xlsx",
         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      )
    st.markdown('---')

    if selected_dates:
        for date in selected_dates:
            total_quantity_date = df[df['Date of State'] == date]['Available Quantity'].sum()
            st.metric(label=f"Total available product quantity for {date}", value=int(total_quantity_date))
        st.markdown('---')

    if not df.empty:
        # Retrieve data for the chart based on selected dates and warehouses
        chart_df = get_chart_data(selected_dates, selected_magazines)
        # Create a line chart using Plotly Express
        fig = px.line(
            chart_df, 
            x='Data_State', # Set X axis to 'Data_State' column
            y='Available_Quantity',  # Set Y axis to 'Available_Quantity' column
            color='Warehouse_Name', # Different line colors for each warehouse
            title='Changes in Available Product Quantity Over Time') # Chart title
        # Update chart layout - set axis titles
        fig.update_layout(xaxis_title='Date', # X axis title
                          yaxis_title='Available Quantity') # Y axis title
        # Ensure Y axis starts from zero 
        fig.update_layout(yaxis=dict(rangemode='tozero'))
        fig.update_layout(xaxis=dict(tickmode='linear', dtick='D1'))
        # Display the chart in the Streamlit app
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
