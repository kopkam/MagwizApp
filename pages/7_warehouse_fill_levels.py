import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

# Function to load available warehouses
def load_available_warehouses():
    conn = sqlite3.connect('db_inventory.db')
    query = "SELECT DISTINCT warehouse_name FROM Warehouses"
    warehouses = pd.read_sql_query(query, conn)['warehouse_name'].tolist()
    conn.close()
    return warehouses

# Function to load data for selected warehouses and date
def load_data(selected_warehouses, selected_date):
    conn = sqlite3.connect('db_inventory.db')

    # Build the SQL query string for warehouses
    placeholders = ', '.join(['?' for _ in selected_warehouses])

    query = f"""
    SELECT 
        w.warehouse_name,
        ROUND((SUM(p.volume_m3 * i.stock_quantity) / w.capacity) * 100, 2) AS fill_percentage
    FROM 
        Warehouses w
    INNER JOIN 
        Inventory i ON w.warehouse_id = i.warehouse_id
    INNER JOIN 
        Products p ON i.product_code = p.product_code
    WHERE
        w.warehouse_name IN ({placeholders})
        AND DATE(i.stock_date) = ?
    GROUP BY 
        w.warehouse_name, w.capacity;
    """
    # SQL query parameters
    params = selected_warehouses + [selected_date]

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Function to create a gauge chart
def create_gauge_chart(value, warehouse):
    colors = ["green", "orange", "red"]
    thresholds = [0, 50, 90, 100]

    def find_color(val, thresholds, colors):
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= val < thresholds[i + 1]:
                return colors[i]
        return colors[-1]

    bar_color = find_color(value, thresholds, colors)
    value_color = find_color(value, thresholds, colors)

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

    fig.update_layout(font={'color': "white", 'family': "Arial"})
    fig.update_traces(number_font_color=value_color)

    return fig

# Function to load available dates
def load_available_dates():
    conn = sqlite3.connect('db_inventory.db')
    query = "SELECT DISTINCT DATE(stock_date) as available_date FROM Inventory ORDER BY available_date ASC"
    dates = pd.read_sql_query(query, conn)['available_date'].tolist()
    conn.close()
    return dates

# Main function
def main():
    # Load available warehouses and dates
    available_warehouses = load_available_warehouses()
    available_dates = load_available_dates()

    # Display the title
    st.title('Warehouse Fill Level Indicator')

    # Date selection
    selected_date = st.selectbox("Select date", available_dates, index=len(available_dates)-1)

    # Warehouse selection using multiselectbox
    selected_warehouses = st.multiselect("Select warehouses", available_warehouses)

    # Check if warehouses have been selected
    if selected_warehouses:
        # Load data for selected warehouses and date
        df = load_data(selected_warehouses, selected_date)

        # Display gauge charts for each warehouse
        for warehouse, percentage in zip(df['warehouse_name'], df['fill_percentage']):
            fig = create_gauge_chart(percentage, warehouse)
            st.write(f"## Gauge for warehouse '{warehouse}'")
            st.plotly_chart(fig)
    else:
        # Load data for all warehouses and date
        df = load_data(available_warehouses, selected_date)

        # Display gauge charts for each warehouse
        for warehouse, percentage in zip(df['warehouse_name'], df['fill_percentage']):
            # Create the gauge chart for the warehouse
            fig = create_gauge_chart(percentage, warehouse)
            # Display the chart title with the warehouse name
            st.write(f"## Gauge for warehouse '{warehouse}'")
            # Display the gauge chart
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
