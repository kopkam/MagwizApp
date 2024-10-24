import streamlit as st
from st_pages import Page, show_pages, add_page_title

def main():
    # Displaying the centered app logo
    left_col, center_col, center_col2, right_col = st.columns(4)
    with center_col:
        st.image('MAGWIZ.png', width=350)
    
    # Displaying text below the logo using HTML code
    st.markdown("<h1 style='text-align: center; color: black;'>Effectively Manage Your Warehouse Inventory</h1>", 
                unsafe_allow_html=True)
    
    # Displaying a dividing line
    st.markdown("---")
    
    # Displaying text below the dividing line
    st.write(
        """
        The simple-to-use Magwiz app is a tool that streamlines the flow of inventory
        in the warehouse. All essential functions in one place!
        """)
    
    # Function description
    st.header('Features:')
    st.markdown("""
    - **Data Exploration (🔍):** Update and browse data related to warehouse activities to better understand trends and patterns.
    - **Inventory Levels (📦):** Track the current inventory levels of products and monitor their changes over time.
    - **Stock Shortages (⚠️):** Receive information about stock shortages and take appropriate actions to resolve them.
    - **ABC Analysis (📊):** Analyze products based on their value and importance to better manage inventory.
    - **Order Timeliness (🚚):** Monitor the timeliness of deliveries and shipments, and identify delays to optimize logistics processes.
    - **Order Fulfillment Time (⏱️):** Track the time it takes to fulfill deliveries and orders to ensure timely deliveries and optimize logistics processes.
    - **Warehouse Fill Levels (📈):** Check warehouse fill levels and make decisions on their optimal usage.
    """)

    st.write("Please select one of the options from the panel on the left side.")

    show_pages(
        [
            Page("main.py", "Home", "🏠"),
            Page("pages/1_data_exploration.py", "Data Exploration", "🔍"),
            Page("pages/2_inventory_levels.py", "Inventory Levels", "📦"),
            Page("pages/3_stock_shortages.py", "Stock Shortages", "⚠️"),
            Page("pages/4_abc_analysis.py", "ABC Analysis", "📊"),
            Page("pages/5_order_timeliness.py", "Order Timeliness", "🚚"),
            Page("pages/6_order_fulfillment_time.py", "Order Fulfillment Time", "⏱️"),
            Page("pages/7_warehouse_fill_levels.py", "Warehouse Fill Levels", "📈")
        ]
    )

if __name__ == "__main__":
    main()