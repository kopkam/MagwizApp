import streamlit as st
import sqlite3
import pandas as pd
import io
import plotly.express as px
from datetime import datetime

# Funkcja do wczytywania danych
def load_data():
    conn = sqlite3.connect('db_zapasy.db')
    query = """
    SELECT
        z.data_zamowienia AS 'Data zamówienia',
        p.kod_produktu,
        p.nazwa_produktu,
        zs.ilosc AS ilosc_sprzedazy
    FROM 
        ZamowieniaSzczegoly zs
    JOIN 
        Zamowienia z ON zs.id_zamowienia = z.id_zamowienia
    JOIN 
        Produkty p ON zs.kod_produktu = p.kod_produktu;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Funkcja do analizy ABC
def analyze_abc(df):
    df['Suma Sprzedaży'] = df.groupby(['nazwa_produktu'])['ilosc_sprzedazy'].transform('sum')
    df['Procent Sprzedaży'] = df['Suma Sprzedaży'] / df['Suma Sprzedaży'].sum() * 100
    df.sort_values(by='Procent Sprzedaży', ascending=False, inplace=True)
    df['Narastająco'] = df['Procent Sprzedaży'].cumsum()
    df['Analiza ABC'] = pd.cut(df['Narastająco'], bins=[0, 20, 50, 100], labels=['A', 'B', 'C'])
    df['Procent Sprzedaży'] = df['Procent Sprzedaży'].round(5).astype(str) + '%'
    df['Narastająco'] = df['Narastająco'].round(5).astype(str) + '%'
    df.drop_duplicates(subset=['nazwa_produktu'], keep='first', inplace=True)
    return df

# Funkcja do wyświetlania metryk
def display_metrics(metric, metric_name):
    st.subheader("Podsumowanie analizy ABC")
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns(2)

    with col1:
        st.metric(label=metric_name[0], value=metric[0])
    with col2:
        st.metric(label=metric_name[1], value=metric[1])
    with col3:
        st.metric(label=metric_name[2], value=metric[2])
    with col4:
        st.metric(label=metric_name[3], value=metric[3])
    with col5:
        st.metric(label=metric_name[4], value=metric[4])

# Funkcja główna
def main():
    st.title('Analiza ABC sprzedaży produktów')

    # Wczytanie danych
    df = load_data()
    df['Data zamówienia'] = pd.to_datetime(df['Data zamówienia']).dt.date

    # Suwaki daty
    min_date = min(df['Data zamówienia'])
    max_date = max(df['Data zamówienia'])
    start_date = st.date_input("Wybierz początkową datę", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Wybierz końcową datę", min_value=min_date, max_value=max_date, value=max_date)
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Sprawdzenie poprawności wybranych dat
    if start_date > end_date:
        st.error("Błąd: Data początkowa nie może być większa niż data końcowa!")
    elif start_date == end_date:
        st.error("Błąd: Data początkowa i końcowa nie mogą być identyczne!")
    else:
        # Filtrowanie danych
        filtered_df = df[(df['Data zamówienia'] >= start_date.date()) & (df['Data zamówienia'] <= end_date.date())]
        abc_df = analyze_abc(filtered_df)
        abc_df.drop(columns=['kod_produktu', 'Data zamówienia', 'ilosc_sprzedazy'], inplace=True)
        abc_df.rename(columns={
            'nazwa_produktu': 'Nazwa Produktu',
            'Suma Sprzedaży': 'Suma Sprzedaży',
            'Procent Sprzedaży': 'Procent Sprzedaży',
            'Narastająco': 'Narastająco',
            'Analiza ABC': 'Analiza ABC'
        }, inplace=True)

        # Wyświetlenie raportu
        st.dataframe((abc_df), hide_index=True)

        # Przycisk do pobierania danych jako pliku Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            abc_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Pobierz jako plik Excel",
            data=output.getvalue(),
            file_name="analiza_abc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.markdown('---')  

        # Podsumowanie analizy ABC
        abc_counts = abc_df['Analiza ABC'].value_counts().sort_index()
        suma_sprzedazy_filtered = abc_df['Suma Sprzedaży'].sum()
        produkty_kategorii = [abc_counts['A'], abc_counts['B'], abc_counts['C'], abc_counts.sum()]
        nazwy_kategorii = ['Liczba produktów dla kategorii A', 'Liczba produktów dla kategorii B', 'Liczba produktów dla kategorii C', 'Liczba unikalnych sprzedanych produktów']
        display_metrics(produkty_kategorii + [suma_sprzedazy_filtered], nazwy_kategorii + ['Całkowita liczba sprzedanych produktów'])
        st.markdown('---')  

        # Wykres
        st.subheader('Procentowe wystąpienie produktów w poszczególnej kategorii')
        abc_counts_percent = abc_df['Analiza ABC'].value_counts(normalize=True) * 100
        fig = px.bar(x=abc_counts_percent.index, y=abc_counts_percent.values, labels={'x': 'Kategoria', 'y': 'Procent wystąpienia'})
        fig.update_traces(texttemplate='%{y:.2f}%', textposition='outside')
        st.plotly_chart(fig)
        st.markdown('---')  

        # TOP produkt
        top_product = abc_df.nlargest(1, 'Suma Sprzedaży').iloc[0]
        top_product_info = f"<div style='display:flex; justify-content: space-between;'><div><h3>TOP Produkt</h3><p>{top_product['Nazwa Produktu']}</p></div><div><h3>Sprzedaż</h3><p>{top_product['Suma Sprzedaży']}</p></div></div>"
        st.markdown(top_product_info, unsafe_allow_html=True)

# Uruchomienie aplikacji
if __name__ == '__main__':
    main()
