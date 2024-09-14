import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import io
from datetime import datetime

# Funkcja do wczytywania danych
def load_data(option):
    # Połączenie z bazą danych SQLite3
    conn = sqlite3.connect('db_zapasy.db')

    if option == "Terminowość dostaw":
        # Zapytanie SQL dla dostawców
        query = """
        SELECT 
            DS.id_dostawy AS 'Numer dostawy',
            D.nazwa_dostawcy AS 'Nazwa dostawcy', 
            DATE(DS.data_zamowienia) AS 'Data zamówienia', 
            DATE(DS.oczekiwana_data_dostawy)  AS 'Oczekiwana data dostawy', 
            DATE(DS.data_dostawy) AS 'Data dostawy', 
            DS.status_dostawy AS 'Status dostawy'
        FROM Dostawy DS
        JOIN Dostawcy D ON DS.id_dostawca = D.id_dostawca;
        """
    elif option == "Terminowość wysyłek":
        # Zapytanie SQL dla klientów
        query = """
        SELECT 
            Z.id_zamowienia AS 'Numer zamówienia',
            K.nazwa_klienta AS 'Nazwa klienta', 
            DATE(Z.data_zamowienia) AS 'Data zamówienia', 
            DATE(Z.oczekiwany_termin_wysylki) AS 'Oczekiwany termin wysyłki', 
            DATE(Z.data_wysylki) AS 'Data Wysyłki', 
            Z.status_wysylki AS 'Status wysyłki'
        FROM Zamowienia Z
        JOIN Klienci K ON Z.id_klient = K.id_klient;
        """

    # Wykonanie zapytania i wczytanie wyników do ramki danych
    df = pd.read_sql_query(query, conn)
    # Zamknięcie połączenia z bazą danych
    conn.close()
    # Zwrócenie ramki danych
    return df

# Wczytanie danych
option = st.sidebar.radio("Wybierz dane do wyświetlenia", ("Terminowość dostaw", "Terminowość wysyłek"))
df = load_data(option)

# Wyświetlenie tytułu
st.title('Wskaźnik terminowości zamówień')

# Funkcja do wyświetlania danych dla dostawców
def display_supplier_data(df):

    st.subheader("Terminowość realizacji dostaw")

    # Wybór wartości do wyświetlenia na wykresie
    selected_values = st.multiselect("Wybierz status dostawy", df['Status dostawy'].unique(), default=[])

    # Konwersja daty na datetime
    df['Data zamówienia'] = pd.to_datetime(df['Data zamówienia']).dt.date

    # Dodanie interaktywnego suwaka daty
    min_date = min(df['Data zamówienia'])
    max_date = max(df['Data zamówienia'])

    # Zabezpieczenie: minimalna data nie może być większa niż maksymalna data
    start_date = st.date_input("Wybierz początkową datę", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Wybierz końcową datę", min_value=min_date, max_value=max_date, value=max_date)

    # Konwersja daty do obiektu datetime
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Sprawdzenie poprawności wybranych dat
    if start_date > end_date:
        st.error("Błąd: Data początkowa nie może być większa niż data końcowa!")
    elif start_date == end_date:
        st.error("Błąd: Data początkowa i końcowa nie mogą być identyczne!")
    else:
        # Filtrowanie danych na podstawie wybranego okresu czasu
        filtered_df = df[(df['Data zamówienia'] >= start_date.date()) & (df['Data zamówienia'] <= end_date.date())]

        # Sprawdzenie, czy którykolwiek filtr został wybrany
        if selected_values:
            # Wyświetlenie ramki danych tylko wtedy, gdy filtr jest wybrany
            st.dataframe(filtered_df[filtered_df['Status dostawy'].isin(selected_values)], hide_index=True)
        else:
            # Wyświetlenie pełnej ramki danych, gdy nie ma żadnych filtrów wybranych
            st.dataframe((filtered_df), hide_index=True)

        # Dodanie przycisku do pobierania danych jako pliku Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Pobierz jako plik Excel",
            data=output.getvalue(),
            file_name="terminowosc_dostawcy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Dodanie linii oddzielającej
        st.markdown("---")
        
# Tworzenie wykresów dla wybranych wartości
    selected_value = 'Zrealizowano na czas'  # Wybrana wartość zawsze będzie 'Zrealizowano na czas'

    # Filtrowanie danych dla wybranej wartości
    filtered_status_df = filtered_df[filtered_df['Status dostawy'] == selected_value]

    # Obliczenie procentowego występowania wybranej wartości
    percent_value = (filtered_df['Status dostawy'] == selected_value).mean() * 100

    # Określenie kolorów dla progów
    value = percent_value
    colors = ["red", "orange", "green"]
    thresholds = [0, 50, 75, 100]

    # Funkcja do znalezienia koloru na podstawie wartości
    def find_color(val, thresholds, colors):
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= val < thresholds[i + 1]:
                return colors[i]
        return colors[-1]

    # Znalezienie koloru dla wartości
    bar_color = find_color(value, thresholds, colors)
    value_color = find_color(value, thresholds, colors)

    # Tworzenie interakcyjnego wykresu prędkościomierza
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

    # Aktualizacja layoutu
    fig.update_layout(font={'color': "white", 'family': "Arial"})

    # Pobranie koloru tła za pomocą CSS
    # Aktualizacja koloru wartości
    fig.update_traces(number_font_color=value_color)

    # Wyświetlenie wykresu z tłem
    st.write(f"## Procent dostaw zrealizowanych na czas w okresie od {start_date.date()} do {end_date.date()}")
    st.plotly_chart(fig)

    # Dodanie linii oddzielającej
    st.markdown("---")

    # Domyślnie wybieramy statusy 'Zrealizowano na czas' i 'Zrealizowano z opóźnieniem'
    selected_values = ['Zrealizowano na czas', 'Zrealizowano z opóźnieniem']

    if not selected_values:
        selected_values = ['Zrealizowano na czas', 'Zrealizowano z opóźnieniem']
    # Sprawdzenie wybranych wartości w selectboxie
    
    for selected_value in selected_values:
        # Filtrowanie danych dla wybranego statusu dostawy
        if selected_value == 'Zrealizowano na czas':
            filtered_status_df = df[df['Status dostawy'] == 'Zrealizowano na czas']
            supplier_label = "Najlepszy dostawca"
            record_label = "Liczba dostaw na czas"
        elif selected_value == 'Zrealizowano z opóźnieniem':
            filtered_status_df = df[df['Status dostawy'] == 'Zrealizowano z opóźnieniem']
            supplier_label = "Najgorszy dostawca"
            record_label = "Liczba opóźnionych dostaw"

        # Filtrowanie danych według wybranych dat
        filtered_status_df = filtered_status_df[(filtered_status_df['Data zamówienia'] >= start_date.date()) & (filtered_status_df['Data zamówienia'] <= end_date.date())]

        # Grupowanie danych według nazwy dostawcy i zliczanie rekordów
        count_by_supplier = filtered_status_df.groupby('Nazwa dostawcy').size().reset_index(name='Liczba rekordów')

        # Znalezienie rekordu z największą lub najmniejszą liczbą rekordów
        if selected_value == 'Zrealizowano na czas':
            max_record = count_by_supplier.loc[count_by_supplier['Liczba rekordów'].idxmax()]
        elif selected_value == 'Zrealizowano z opóźnieniem':
            max_record = count_by_supplier.loc[count_by_supplier['Liczba rekordów'].idxmax()]

        # Tworzenie informacji o dostawcy w podobnym stylu
        #supplier_info = f"<div style='display:flex; justify-content: space-between;'><div style='display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center;'><h3 style='word-wrap: break-word;'>{supplier_label}</h3><p>{max_record['Nazwa dostawcy']}</p></div><div style='width: 1px; background-color: #ccc; margin: 0 10px;'></div><div style='display: flex; flex-direction: column; justify-content: center; align-items: center;'><h3>{record_label}</h3><p>{max_record['Liczba rekordów']}</p></div></div>"
        supplier_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>{supplier_label}</h3><p>{max_record['Nazwa dostawcy']}</p></div><div style='text-align: center; margin: auto;'><h3>{record_label}</h3><p>{max_record['Liczba rekordów']}</p></div></div>"

        st.markdown(supplier_info, unsafe_allow_html=True)

# Funkcja do wyświetlania danych do klientów
def display_customer_data(df):

    st.subheader("Terminowość realizacji wysyłek")

    # Wybór wartości do wyświetlenia na wykresie
    selected_values = st.multiselect("Wybierz status wysyłki", df['Status wysyłki'].unique(), default=[])

    # Konwersja daty na datetime
    df['Data zamówienia'] = pd.to_datetime(df['Data zamówienia']).dt.date

    # Dodanie interaktywnego suwaka daty
    min_date = min(df['Data zamówienia'])
    max_date = max(df['Data zamówienia'])

    # Zabezpieczenie: minimalna data nie może być większa niż maksymalna data
    start_date = st.date_input("Wybierz początkową datę", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Wybierz końcową datę", min_value=min_date, max_value=max_date, value=max_date)

    # Konwersja daty do obiektu datetime
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Sprawdzenie poprawności wybranych dat
    if start_date > end_date:
        st.error("Błąd: Data początkowa nie może być większa niż data końcowa!")
    elif start_date == end_date:
        st.error("Błąd: Data początkowa i końcowa nie mogą być identyczne!")
    else:
        # Filtrowanie danych na podstawie wybranego okresu czasu
        filtered_df = df[(df['Data zamówienia'] >= start_date.date()) & (df['Data zamówienia'] <= end_date.date())]

        # Sprawdzenie, czy którykolwiek filtr został wybrany
        if selected_values:
            # Wyświetlenie ramki danych tylko wtedy, gdy filtr jest wybrany
            st.dataframe(filtered_df[filtered_df['Status wysyłki'].isin(selected_values)], hide_index=True)
        else:
            # Wyświetlenie pełnej ramki danych, gdy nie ma żadnych filtrów wybranych
            st.dataframe((filtered_df), hide_index=True)

        # Dodanie przycisku do pobierania danych jako pliku Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Pobierz jako plik Excel",
            data=output.getvalue(),
            file_name="terminowosc_klienci.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Dodanie linii oddzielającej
        st.markdown("---")
        
    # Tworzenie wykresów dla wybranych wartości
    selected_value = 'Zrealizowano na czas'  # Wybrana wartość zawsze będzie 'Zrealizowano na czas'

    # Filtrowanie danych dla wybranej wartości
    filtered_status_df = filtered_df[filtered_df['Status wysyłki'] == selected_value]

    # Obliczenie procentowego występowania wybranej wartości
    percent_value = (filtered_df['Status wysyłki'] == selected_value).mean() * 100

    # Określenie kolorów dla progów
    value = percent_value
    colors = ["red", "orange", "green"]
    thresholds = [0, 50, 75, 100]

    # Funkcja do znalezienia koloru na podstawie wartości
    def find_color(val, thresholds, colors):
        for i in range(len(thresholds) - 1):
            if thresholds[i] <= val < thresholds[i + 1]:
                return colors[i]
        return colors[-1]

    # Znalezienie koloru dla wartości
    bar_color = find_color(value, thresholds, colors)
    value_color = find_color(value, thresholds, colors)

    # Tworzenie interakcyjnego wykresu prędkościomierza
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

    # Aktualizacja layoutu
    fig.update_layout(font={'color': "white", 'family': "Arial"})

    # Pobranie koloru tła za pomocą CSS
    # Aktualizacja koloru wartości
    fig.update_traces(number_font_color=value_color)

    # Wyświetlenie wykresu z tłem
    st.write(f"## Procent wysyłek zrealizowanych na czas w okresie od {start_date.date()} do {end_date.date()}")
    st.plotly_chart(fig)

    # Dodanie linii oddzielającej
    st.markdown("---")

    # Domyślnie wybieramy statusy 'Zrealizowano na czas' i 'Zrealizowano z opóźnieniem'
    if not selected_values:
        selected_values = ['Zrealizowano na czas', 'Zrealizowano z opóźnieniem']  # Jeśli nic nie jest wybrane, wybieramy oba statusy

    for selected_value in selected_values:
        # Filtrowanie danych dla wybranego statusu wysyłki
        if selected_value == 'Zrealizowano na czas':
            filtered_status_df = df[df['Status wysyłki'] == 'Zrealizowano na czas']
            customer_label = "Najlepiej obsługiwany klient"
            record_label = "Liczba wysłanych na czas zamówień"
        elif selected_value == 'Zrealizowano z opóźnieniem':
            filtered_status_df = df[df['Status wysyłki'] == 'Zrealizowano z opóźnieniem']
            customer_label = "Najgorzej obsługiwany klient"
            record_label = "Liczba opóźnionych zamówień"
        else:
            filtered_status_df = df[df['Status wysyłki'] == 'Zrealizowano z opóźnieniem']
            customer_label = "Najgorzej obsługiwany klient"
            record_label = "Liczba opóźnionych zamówień"

        # Filtrowanie danych według wybranych dat
        filtered_status_df = filtered_status_df[(filtered_status_df['Data zamówienia'] >= start_date.date()) & (filtered_status_df['Data zamówienia'] <= end_date.date())]

        # Grupowanie danych według nazwy klienta i zliczanie rekordów
        count_by_customer = filtered_status_df.groupby('Nazwa klienta').size().reset_index(name='Liczba rekordów')

        # Znalezienie rekordu z największą lub najmniejszą liczbą rekordów
        if selected_value == 'Zrealizowano na czas':
            max_record = count_by_customer.loc[count_by_customer['Liczba rekordów'].idxmax()]
        elif selected_value == 'Zrealizowano z opóźnieniem':
            max_record = count_by_customer.loc[count_by_customer['Liczba rekordów'].idxmax()]

        # Tworzenie informacji o kliencie w podobnym stylu
        customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>{customer_label}</h3><p>{max_record['Nazwa klienta']}</p></div><div style='text-align: center;'><h3>{record_label}</h3><p>{max_record['Liczba rekordów']}</p></div></div>"
        st.markdown(customer_info, unsafe_allow_html=True)

# Wybierz, którą opcję wyświetlić
if option == "Terminowość dostaw":
    display_supplier_data(df)
elif option == "Terminowość wysyłek":
    display_customer_data(df)
