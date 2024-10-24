import streamlit as st
import pandas as pd
import sqlite3
import os
import datetime

# Function to fetch names of existing tables from the database
def get_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

# Function to fetch names of existing tables from the database along with Excel file size and last modification date
def get_table_names_with_excel_info(conn, folder_path):
    # Create a cursor to execute SQL commands
    cursor = conn.cursor()
    # Execute SQL query to fetch names of all tables from the SQLite database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    # Fetch query results (table names)
    tables = cursor.fetchall()
    # List to store information about tables
    table_names_with_info = []
    # Iterate over each table name
    for table in tables:
        table_name = table[0]  # Get the table name
        excel_file = f"{table_name}.xlsx"  # Create the corresponding Excel file name
        excel_path = os.path.join(folder_path, excel_file)  # Create the path to the Excel file
        # Check if the Excel file exists
        if os.path.exists(excel_path):
            size_bytes = os.path.getsize(excel_path)  # Get the file size in bytes
            size_mb = size_bytes / (1024 * 1024)  # Convert the size to megabytes
            modification_time = os.path.getmtime(excel_path)  # Get the file modification time
            modification_time_str = datetime.datetime.fromtimestamp(modification_time).strftime(
                '%d-%m-%Y %H:%M:%S')  # Format the modification date
            # Add table information to the list
            table_names_with_info.append((table_name, size_mb, modification_time_str))
    # Return the list with table information
    return table_names_with_info

# Function to fetch records from the selected table
def get_first_last_records(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)

    return df

# Function to remove duplicates from the first column of a table
def remove_duplicates(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    primary_key = df.columns[0]
    num_records_before = len(df)
    df.drop_duplicates(subset=primary_key, keep='first', inplace=True)
    num_records_after = len(df)
    num_duplicates_removed = num_records_before - num_records_after
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    
    return num_duplicates_removed

# Function to update data from Excel files
def update_data(conn):
    folder_path = 'Data'
    excel_files = {
        'suppliers.xlsx': 'Suppliers',
        'products.xlsx': 'Products',
        'warehouses.xlsx': 'Warehouses',
        'warehouse_stock.xlsx': 'WarehouseStock',
        'customers.xlsx': 'Customers',
        'orders.xlsx': 'Orders',
        'order_details.xlsx': 'OrderDetails',
        'deliveries.xlsx': 'Deliveries',
        'delivery_details.xlsx': 'DeliveryDetails'
    }

    for excel_file, table_name in excel_files.items():
        excel_path = os.path.join(folder_path, excel_file)
        if os.path.exists(excel_path):
            existing_data = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            new_data = pd.read_excel(excel_path)
            
            # Remove duplicates in the first column
            num_duplicates_removed = remove_duplicates(conn, table_name)
            if num_duplicates_removed > 0:
                st.write(f"Removed {num_duplicates_removed} duplicates from the '{table_name}' table.")
            
            # Add new records
            new_records = new_data[~new_data.iloc[:, 0].isin(existing_data.iloc[:, 0])]
            num_added_records = len(new_records)
            new_records.to_sql(table_name, conn, if_exists='append', index=False)
            st.write(f"Added {num_added_records} new records to the '{table_name}' table.")
            
            # Remove records that do not exist in the Excel file but exist in the database
            records_to_delete = existing_data[~existing_data.iloc[:, 0].isin(new_data.iloc[:, 0])]
            num_deleted_records = len(records_to_delete)
            if num_deleted_records > 0:
                for index, row in records_to_delete.iterrows():
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {table_name} WHERE {existing_data.columns[0]} = ?", (row[existing_data.columns[0]],))
                    conn.commit()
                st.write(f"Deleted {num_deleted_records} records from the '{table_name}' table.")
        else:
            st.write(f"The file '{excel_file}' does not exist. Skipping...")


# Connection to the SQLite database
conn = sqlite3.connect('DB_INVENTORY.db')


# Streamlit page
def main():
    st.title('Updating data retrieved from Excel files')

    # Button to update files
    update_button = st.button("Update data")
    st.markdown('---')

    if update_button:
        messages_to_clear = st.empty()  # Store message state
        update_data(conn)
        st.write("Update completed.")
        # Display a button to clear messages only if the update was performed
        st.button("Clear messages")

    st.title('Available Excel files')
    
    # Buttons to show/hide tables
    show_files = st.button('Show information')
    hide_files = False

    if show_files:
        folder_path = 'Data'
        table_names_with_info = get_table_names_with_excel_info(conn, folder_path)
        if table_names_with_info:
            for table_name, size_mb, modification_time_str in table_names_with_info:
                st.write(f"- {table_name}.xlsx (size: {size_mb:.2f} MB, last modification: {modification_time_str})")
        else:
            st.write("No files.")
        hide_files = st.button('Hide information')

    if hide_files:
        st.text("Files hidden.")

    st.markdown('---')
    st.title('Displaying file content')

    table_names = get_table_names(conn)
    selected_table = st.selectbox('Select available file', table_names)
    st.write(f"Selected file: {selected_table}")

    show_records = st.button('Show content')
    hide_records = False

    if show_records:
        df = get_first_last_records(conn, selected_table)
        st.write("Current data:")
        st.dataframe(df, hide_index=True)
        hide_records = st.button('Hide content')

    if hide_records:
        st.text("Content hidden.")

if __name__ == "__main__":
    main()
