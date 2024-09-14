import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go

# Funkcja do wczytywania dostępnych magazynów
def load_available_warehouses():
    conn = sqlite3.connect('db_zapasy.db')
    query = "SELECT DISTINCT nazwa_magazynu FROM Magazyny"
    warehouses = pd.read_sql_query(query, conn)['nazwa_magazynu'].tolist()
    conn.close()
    return warehouses

# Funkcja do wczytywania danych dla wybranych magazynów i daty
def load_data(selected_warehouses, selected_date):
    conn = sqlite3.connect('db_zapasy.db')

    # Zbudowanie ciągu zapytania SQL dla magazynów
    placeholders = ', '.join(['?' for _ in selected_warehouses])

    query = f"""
    SELECT 
        m.nazwa_magazynu,
        ROUND((SUM(p.objetosc_m3 * sm.ilosc_na_stanie) / m.pojemnosc) * 100, 2) AS procent_wypelnienia
    FROM 
        Magazyny m
    INNER JOIN 
        StanyMagazynowe sm ON m.id_magazyn = sm.id_magazyn
    INNER JOIN 
        Produkty p ON sm.kod_produktu = p.kod_produktu
    WHERE
        m.nazwa_magazynu IN ({placeholders})
        AND DATE(sm.data_stanu) = ?
    GROUP BY 
        m.nazwa_magazynu, m.pojemnosc;
    """
    # Parametry zapytania SQL
    params = selected_warehouses + [selected_date]

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# Funkcja do tworzenia wykresu prędkościomierza
def create_gauge_chart(value, magazyn):
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

# Funkcja do wczytywania dostępnych dat
def load_available_dates():
    conn = sqlite3.connect('db_zapasy.db')
    query = "SELECT DISTINCT DATE(data_stanu) as available_date FROM StanyMagazynowe ORDER BY available_date ASC"
    dates = pd.read_sql_query(query, conn)['available_date'].tolist()
    conn.close()
    return dates

# Główna funkcja
def main():
    # Wczytanie dostępnych magazynów i dat
    available_warehouses = load_available_warehouses()
    available_dates = load_available_dates()

    # Wyświetlenie tytułu
    st.title('Wskaźnik wypełnienia magazynów')

    # Wybór daty
    selected_date = st.selectbox("Wybierz datę", available_dates, index=len(available_dates)-1)

    # Wybór magazynów za pomocą multiselectboxa
    selected_warehouses = st.multiselect("Wybierz magazyny", available_warehouses)

    # Sprawdzenie, czy zostały wybrane magazyny
    if selected_warehouses:
        # Wczytanie danych dla wybranych magazynów i daty
        df = load_data(selected_warehouses, selected_date)

        # Wyświetlenie wykresów prędkościomierza dla każdego magazynu
        for magazyn, procent in zip(df['nazwa_magazynu'], df['procent_wypelnienia']):
            fig = create_gauge_chart(procent, magazyn)
            st.write(f"## Wykres dla magazynu '{magazyn}'")
            st.plotly_chart(fig)
    else:
        # Wczytanie danych dla wszystkich magazynów i daty
        df = load_data(available_warehouses, selected_date)

        # Wyświetlenie wykresów prędkościomierza dla każdego magazynu
        for magazyn, procent in zip(df['nazwa_magazynu'], df['procent_wypelnienia']):
            # Tworzenie wykresu prędkościomierza dla danego magazynu
            fig = create_gauge_chart(procent, magazyn)
            # Wyświetlenie tytułu wykresu zawierającego nazwę magazynu
            st.write(f"## Wykres dla magazynu '{magazyn}'")
            # Wyświetlenie wykresu prędkościomierza
            st.plotly_chart(fig)

if __name__ == "__main__":
    main()
