import sqlite3
import pandas as pd
import streamlit as st
import io
import plotly.express as px

def connect_db():
    return sqlite3.connect('db_zapasy.db')

def get_data(selected_dates, selected_magazines, product_name):
    conn = connect_db()
    dates_filter = "'" + "', '".join(selected_dates) + "'"
    magazines_filter = "'" + "', '".join(selected_magazines) + "'" if selected_magazines else "ALL"
    where_clause = f"DATE(s.data_stanu) IN ({dates_filter})"
    if selected_magazines:
        where_clause += f" AND m.nazwa_magazynu IN ({magazines_filter})"
    if product_name:
        where_clause += f" AND p.nazwa_produktu LIKE '%{product_name}%'"
    query = f"""
    SELECT 
        DATE(s.data_stanu) AS Data_Stanu,
        p.nazwa_produktu AS Nazwa_Produktu,
        m.nazwa_magazynu AS Nazwa_Magazynu,
        s.ilosc_dostepna AS Ilosc_Dostepna
    FROM 
        StanyMagazynowe s
    JOIN 
        Produkty p ON s.kod_produktu = p.kod_produktu
    JOIN 
        Magazyny m ON s.id_magazyn = m.id_magazyn
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
    where_clause = f"DATE(s.data_stanu) IN ({dates_filter})"
    if selected_magazines:
        where_clause += f" AND m.nazwa_magazynu IN ({magazines_filter})"
    query = f"""
    SELECT 
        DATE(s.data_stanu) AS Data_Stanu,
        m.nazwa_magazynu AS Nazwa_Magazynu,
        SUM(s.ilosc_dostepna) AS Ilosc_Dostepna
    FROM 
        StanyMagazynowe s
    JOIN 
        Magazyny m ON s.id_magazyn = m.id_magazyn
    WHERE 
        {where_clause}
    GROUP BY 
        DATE(s.data_stanu), m.nazwa_magazynu;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    conn = connect_db()
    dates_query = "SELECT DISTINCT DATE(data_stanu) AS data_stanu FROM StanyMagazynowe;"
    dates = pd.read_sql_query(dates_query, conn)['data_stanu'].tolist()
    magazines_query = "SELECT DISTINCT nazwa_magazynu FROM Magazyny;"
    magazines = pd.read_sql_query(magazines_query, conn)['nazwa_magazynu'].tolist()
    conn.close()
    latest_date = max(dates) if dates else None

    st.write("# Stan zapasów na wybrany dzień")
    selected_dates = st.multiselect("Wybierz daty:", dates, default=[latest_date] if latest_date else [])
    selected_magazines = st.multiselect("Wybierz magazyny:", magazines)
    product_name = st.text_input("Wprowadź nazwę produktu do filtrowania:")
    if not selected_dates and latest_date:
        selected_dates = [latest_date]
    df = get_data(selected_dates, selected_magazines, product_name)
    df = df.rename(columns={"Data_Stanu": "Data stanu", "Nazwa_Produktu": "Nazwa produktu", "Nazwa_Magazynu": "Nazwa magazynu", "Ilosc_Dostepna": "Dostępna ilość"})
    st.dataframe(df, hide_index=True)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
         df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    st.download_button(
          label="Pobierz jako plik Excel",
          data=output.getvalue(),
          file_name="stany_zapasow.xlsx",
         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      )
    st.markdown('---')

    if selected_dates:
        for date in selected_dates:
            total_quantity_date = df[df['Data stanu'] == date]['Dostępna ilość'].sum()
            st.metric(label=f"Łączna ilość dostęnych produktów dla daty {date}", value=total_quantity_date)
        st.markdown('---')

    if not df.empty:
        chart_df = get_chart_data(selected_dates, selected_magazines)
        fig = px.line(chart_df, x='Data_Stanu', y='Ilosc_Dostepna', color='Nazwa_Magazynu', title='Zmiana ilości dostępnych produktów w wybranym czasie')
        fig.update_layout(xaxis_title='Data', yaxis_title='Dostępna ilość')
        fig.update_layout(yaxis=dict(rangemode='tozero'))
        fig.update_layout(xaxis=dict(tickmode='linear', dtick='D1'))
        st.plotly_chart(fig)

if __name__ == "__main__":
    main()
