import streamlit as st
import sqlite3
import pandas as pd
import io
import plotly.graph_objects as go
import plotly.express as px

# Funkcja do nawiązywania połączenia z bazą danych
def connect_db():
    conn = sqlite3.connect('db_zapasy.db')
    return conn

# Funkcja do ładowania danych
def load_data(conn):
    query = """
        SELECT DATE(sm.data_stanu) AS 'Dzień Stanu',
               p.nazwa_produktu AS 'Nazwa Produktu',
               sm.ilosc_dostepna AS 'Ilość Dostępna',
               p.zapas_bezpieczenstwa AS 'Zapas Bezpieczeństwa'
        FROM StanyMagazynowe sm
        JOIN Produkty p ON sm.kod_produktu = p.kod_produktu
        WHERE sm.ilosc_dostepna < p.zapas_bezpieczenstwa
        ORDER BY sm.data_stanu, p.nazwa_produktu
    """
    df = pd.read_sql_query(query, conn)
    df['Dzień Stanu'] = pd.to_datetime(df['Dzień Stanu'])
    df['Dzień Stanu'] = df['Dzień Stanu'].dt.strftime('%d-%m-%Y')
    return df

# Funkcja do generowania wykresu
def generate_plot(df, selected_dates, search_term):
    fig = go.Figure()
    
    # Definiowanie palety kolorów dla słupków
    colors = px.colors.qualitative.Plotly
    
    # Sortowanie wybranych dat rosnąco
    selected_dates.sort()

    for i, date in enumerate(selected_dates):
        filtered_df = df[df['Dzień Stanu'] == date]

        if search_term:
            filtered_df = filtered_df[filtered_df['Nazwa Produktu'].str.contains(search_term, case=False)]

        shortages = abs(filtered_df['Ilość Dostępna'] - filtered_df['Zapas Bezpieczeństwa']).sum()

        fig.add_trace(go.Bar(
            name=f'{date}',
            x=['Ilość Dostępna', 'Braki Magazynowe'],
            y=[filtered_df['Ilość Dostępna'].sum(), shortages],
            marker_color=colors[i % len(colors)]  # Użyj reszty z dzielenia do cyklicznego wyboru kolorów, jeśli jest więcej dat niż kolorów
        ))

    fig.update_layout(title='Ilość Dostępna vs. Braki Magazynowe', barmode='group')
    return fig

# Funkcja do pobierania danych i generowania wykresu
def main():
    st.title('Wyświetlanie produktów wymagających zamówienia')

    conn = connect_db()
    df = load_data(conn)
    conn.close()

    latest_date = df['Dzień Stanu'].max()

    selected_dates = st.multiselect('Wybierz daty do filtrowania:', df['Dzień Stanu'].unique(), default=[latest_date])

    # Jeśli nie wybrano żadnej daty, użyj najnowszej dostępnej daty
    if not selected_dates:
        selected_dates = [latest_date]

    search_term = st.text_input("Wprowadź nazwę produktu do filtrowania:")

    # Wyświetlanie tabeli danych
    filtered_df = df[df['Dzień Stanu'].isin(selected_dates)]
    if search_term:
        filtered_df = filtered_df[filtered_df['Nazwa Produktu'].str.contains(search_term, case=False)]
    st.dataframe(filtered_df.drop(columns=['Dzień Stanu']), hide_index=True)

    # Dodanie przycisku do pobierania danych jako pliku Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)
    st.download_button(
        label="Pobierz jako plik Excel",
        data=output.getvalue(),
        file_name="braki_magazynowe.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.markdown('---')

    # Liczba braków magazynowych dla każdej wybranej daty
    for date in selected_dates:
        filtered_date_df = filtered_df[filtered_df['Dzień Stanu'] == date]
        shortages_date = abs(filtered_date_df['Ilość Dostępna'] - filtered_date_df['Zapas Bezpieczeństwa']).sum()
        st.metric(label=f"Braki magazynowe dla daty {date}", value=int(shortages_date))

    st.markdown('---')
    # Generowanie wykresu
    fig = generate_plot(df, selected_dates, search_term)
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
