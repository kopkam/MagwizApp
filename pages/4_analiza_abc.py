import streamlit as st
import sqlite3
import pandas as pd
import io
import plotly.express as px
from datetime import datetime

# Function to load data
def load_data():
    conn = sqlite3.connect('db_inventory.db')
    query = """
    SELECT
        o.order_date AS 'Order Date',
        p.product_code AS 'Product Code',
        p.product_name AS 'Product Name',
        od.quantity AS 'Sales Quantity'
    FROM 
        OrderDetails od
    JOIN 
        Orders o ON od.order_id = o.order_id
    JOIN 
        Products p ON od.product_code = p.product_code;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Function to perform ABC analysis
def analyze_abc(df):
    # Calculate total sales for each product
    df['Total Sales'] = df.groupby(['Product Name'])['Sales Quantity'].transform('sum')
    # Calculate percentage share of sales for each product
    df['Sales Percentage'] = df['Total Sales'] / df['Total Sales'].sum() * 100
    # Sort data by sales percentage in descending order
    df.sort_values(by='Sales Percentage', ascending=False, inplace=True)
    # Calculate cumulative percentage of sales
    df['Cumulative Percentage'] = df['Sales Percentage'].cumsum()
    # Assign ABC categories based on cumulative sales percentage
    df['ABC Category'] = pd.cut(df['Cumulative Percentage'], bins=[0, 20, 50, 100], labels=['A', 'B', 'C'])
    # Round sales percentages and cumulative percentage, and add '%' symbol
    df['Sales Percentage'] = df['Sales Percentage'].round(2).astype(str) + '%'
    df['Cumulative Percentage'] = df['Cumulative Percentage'].round(2).astype(str) + '%'
    return df

# Function to display metrics
def display_metrics(metrics, metric_names):
    st.subheader("ABC Analysis Summary")
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    with col1:
        st.metric(label=metric_names[0], value=metrics[0])
    with col2:
        st.metric(label=metric_names[1], value=metrics[1])
    with col3:
        st.metric(label=metric_names[2], value=metrics[2])
    with col4:
        st.metric(label=metric_names[3], value=metrics[3])
    with col5:
        st.metric(label=metric_names[4], value=metrics[4])

# Main function
def main():
    st.title('ABC Analysis of Product Sales')

    # Load data
    df = load_data()
    df['Order Date'] = pd.to_datetime(df['Order Date']).dt.date

    # Date range sliders
    min_date = min(df['Order Date'])
    max_date = max(df['Order Date'])
    start_date = st.date_input("Select start date", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Select end date", min_value=min_date, max_value=max_date, value=max_date)
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Check date validity
    if start_date > end_date:
        st.error("Error: Start date cannot be later than the end date!")
    elif start_date == end_date:
        st.error("Error: Start date and end date cannot be the same!")
    else:
        # Filter data by selected dates
        filtered_df = df[(df['Order Date'] >= start_date.date()) & (df['Order Date'] <= end_date.date())]
        abc_df = analyze_abc(filtered_df)
    
        abc_df.drop(columns=['product_code', 'Order Date', 'sales_quantity'], inplace=True)
        abc_df.rename(columns={
            'product_name': 'Product Name',
            'Sales Total': 'Sales Total',
            'Sales Percentage': 'Sales Percentage',
            'Cumulative': 'Cumulative',
            'ABC Analysis': 'ABC Analysis'
        }, inplace=True)

        # Display filtered data as a report
        st.dataframe(abc_df, hide_index=True)

        # Button to download data as Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            abc_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Download as Excel file",
            data=output.getvalue(),
            file_name="abc_analysis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown('---')  

        # ABC Analysis summary
        abc_counts = abc_df['ABC Category'].value_counts().sort_index()
        total_sales_filtered = abc_df['Total Sales'].sum()
        products_in_category = [abc_counts['A'], abc_counts['B'], abc_counts['C'], abc_counts.sum()]
        category_names = ['Number of products in category A', 'Number of products in category B', 'Number of products in category C', 'Total number of unique sold products']
        display_metrics(products_in_category + [total_sales_filtered], category_names + ['Total sales'])

        st.markdown('---')  

        # Category percentage chart
        st.subheader('Percentage occurrence of products in each category')
        abc_counts_percent = abc_df['ABC Category'].value_counts(normalize=True) * 100
        fig = px.bar(x=abc_counts_percent.index, y=abc_counts_percent.values, labels={'x': 'Category', 'y': 'Percentage Occurrence'})
        fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
        st.plotly_chart(fig)
        st.markdown('---')  

        # Display top product
        top_product = abc_df.nlargest(1, 'Total Sales').iloc[0]
        top_product_info = f"<div style='display:flex; justify-content: space-between;'><div><h3>Top Product</h3><p>{top_product['Product Name']}</p></div><div><h3>Sales</h3><p>{top_product['Total Sales']}</p></div></div>"
        st.markdown(top_product_info, unsafe_allow_html=True)

# Run the app
if __name__ == '__main__':
    main()
