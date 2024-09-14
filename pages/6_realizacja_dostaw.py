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

    if option == "Czas realizacji dostaw":
        # Zapytanie SQL dla danych dostawcy
        query = """
        SELECT 
            DS.id_dostawy AS 'Numer dostawy',
            D.nazwa_dostawcy AS 'Nazwa dostawcy', 
            DATE(DS.data_zamowienia) AS 'Data zamówienia', 
            DATE(DS.data_dostawy) AS 'Data dostawy', 
            (julianday(DS.data_dostawy) - julianday(DS.data_zamowienia)) AS 'Liczba dni realizacji'
        FROM Dostawy DS
        JOIN Dostawcy D ON DS.id_dostawca = D.id_dostawca;
        """
    elif option == "Czas realizacji wysyłek":
        # Zapytanie SQL dla danych klienta
        query = """
        SELECT 
            Z.id_zamowienia AS 'Numer zamówienia',
            K.nazwa_klienta AS 'Nazwa klienta', 
            DATE(Z.data_zamowienia) AS 'Data zamówienia', 
            DATE(Z.data_wysylki) AS 'Data Wysyłki', 
            (julianday(Z.data_wysylki) - julianday(Z.data_zamowienia)) AS 'Liczba dni realizacji'
        FROM Zamowienia Z
        JOIN Klienci K ON Z.id_klient = K.id_klient;
        """

    # Wykonanie zapytania i wczytanie wyników do DataFrame
    df = pd.read_sql_query(query, conn)

    # Zamknięcie połączenia z bazą danych
    conn.close()

    return df

# Wczytanie danych na podstawie wyboru użytkownika
option = st.sidebar.radio("Wybierz dane do wyświetlenia", ("Czas realizacji dostaw", "Czas realizacji wysyłek"))
df = load_data(option)

# Wyświetlenie tytułu
st.title('Wskaźnik czasu realizacji zamówień')

# Wyświetlenie danych dla dostawców
if option == "Czas realizacji dostaw":
    st.subheader("Czas trwania realizacji dostaw")
        
    # Konwersja daty na datetime
    df['Data zamówienia'] = pd.to_datetime(df['Data zamówienia']).dt.date

    # Interaktywny suwak daty
    min_date = min(df['Data zamówienia'])
    max_date = max(df['Data zamówienia'])
    start_date = st.date_input("Wybierz początkową datę", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Wybierz końcową datę", min_value=min_date, max_value=max_date, value=max_date)

    # Konwersja daty na obiekt datetime
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Sprawdzenie poprawności daty
    if start_date > end_date:
        st.error("Błąd: Data początkowa nie może być większa niż data końcowa!")
    elif start_date == end_date:
        st.error("Błąd: Data początkowa i końcowa nie mogą być identyczne!")
    else:
        # Filtrowanie danych na podstawie wybranego zakresu dat
        filtered_df = df[(df['Data zamówienia'] >= start_date.date()) & (df['Data zamówienia'] <= end_date.date())]
        
        # Wyświetlenie filtrowanych danych
        st.dataframe(filtered_df, hide_index=True)

        # Obliczenie czasu trwania cyklu
        filtered_df['Czas trwania cyklu'] = (pd.to_datetime(filtered_df['Data dostawy']) - pd.to_datetime(filtered_df['Data zamówienia'])).dt.days

        # Dodanie przycisku pobierania Excela
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Pobierz jako plik Excel",
            data=output.getvalue(),
            file_name="czas_trwania_dostawy.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown('---')

        # Średni czas realizacji cyklu
        average_cycle_time = filtered_df['Czas trwania cyklu'].mean()
        # Średni czas realizacji cyklu w godzinach
        average_cycle_time_hours = average_cycle_time * 24
        st.subheader(f"Średni czas realizacji dostaw od {start_date.date()} do {end_date.date()}")

        col1, col2 = st.columns(2)
        with col1:
            st.metric('', f"{average_cycle_time:.2f} (dni)", label_visibility='visible')
        with col2:
            st.metric('', f"{average_cycle_time_hours:.2f} (godziny)", label_visibility='visible')

        st.markdown('---')
    
    # Obliczenie średniego czasu dostawy dla każdego dostawcy
    average_delivery_time = filtered_df.groupby('Nazwa dostawcy')['Czas trwania cyklu'].mean().reset_index()
    # Znalezienie dostawcy z najdłuższym średnim czasem dostawy
    slowest_customer = average_delivery_time.loc[average_delivery_time['Czas trwania cyklu'].idxmax()]
    # Przygotowanie informacji o najwolniejszym dostawcy w formacie HTML
    slowest_customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Najwolniejszy dostawca</h3><p>{slowest_customer['Nazwa dostawcy']}</p></div><div style='text-align: center;'><h3>Średni czas realizacji dostaw (dni) </h3><p>{slowest_customer['Czas trwania cyklu']:.2f}</p></div></div>"
    fastest_customer = average_delivery_time.loc[average_delivery_time['Czas trwania cyklu'].idxmin()]
    fastest_customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Najszybszy dostawca</h3><p>{fastest_customer['Nazwa dostawcy']}</p></div><div style='text-align: center;'><h3>Średni czas realizacji dostaw (dni) </h3><p>{fastest_customer['Czas trwania cyklu']:.2f}</p></div></div>"
    st.markdown(fastest_customer_info, unsafe_allow_html=True)
    # Wyświetlenie informacji o najwolniejszym dostawcy na stronie za pomocą Streamlit
    st.markdown(slowest_customer_info, unsafe_allow_html=True)

# Wyświetlenie danych dla klientów
elif option == "Czas realizacji wysyłek":
    st.subheader("Czas trwania realizacji wysyłek")

    # Konwersja daty na datetime
    df['Data zamówienia'] = pd.to_datetime(df['Data zamówienia']).dt.date

    # Interaktywny suwak daty
    min_date = min(df['Data zamówienia'])
    max_date = max(df['Data zamówienia'])
    start_date = st.date_input("Wybierz początkową datę", min_value=min_date, max_value=max_date, value=min_date)
    end_date = st.date_input("Wybierz końcową datę", min_value=min_date, max_value=max_date, value=max_date)

    # Konwersja daty na obiekt datetime
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = datetime.combine(end_date, datetime.max.time())

    # Sprawdzenie poprawności daty
    if start_date > end_date:
        st.error("Błąd: Data początkowa nie może być większa niż data końcowa!")
    elif start_date == end_date:
        st.error("Błąd: Data początkowa i końcowa nie mogą być identyczne!")
    else:
        # Filtrowanie danych na podstawie wybranego zakresu dat
        filtered_df = df[(df['Data zamówienia'] >= start_date.date()) & (df['Data zamówienia'] <= end_date.date())]
        
        # Wyświetlenie filtrowanych danych
        st.dataframe(filtered_df, hide_index=True)

        # Obliczenie czasu trwania cyklu
        filtered_df['Czas trwania cyklu'] = (pd.to_datetime(filtered_df['Data Wysyłki']) - pd.to_datetime(filtered_df['Data zamówienia'])).dt.days

        # Dodanie przycisku pobierania Excela
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)
        st.download_button(
            label="Pobierz jako plik Excel",
            data=output.getvalue(),
            file_name="czas_trwania_wysylki.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.markdown('---')

        # Średni czas realizacji cyklu
        average_cycle_time = filtered_df['Czas trwania cyklu'].mean()
        # Średni czas realizacji cyklu w godzinach
        average_cycle_time_hours = average_cycle_time * 24
        st.subheader(f"Średni czas realizacji wysyłek od {start_date.date()} do {end_date.date()}")
        col1, col2 = st.columns(2)

        with col1:
            st.metric('', f"{average_cycle_time:.2f} (dni)", label_visibility='visible')
        with col2:
            st.metric('', f"{average_cycle_time_hours:.2f} (godziny)", label_visibility='visible')

    st.markdown('---')

    # Średni czas wysyłki dla każdego klienta
    average_delivery_time = filtered_df.groupby('Nazwa klienta')['Czas trwania cyklu'].mean().reset_index()
    slowest_customer = average_delivery_time.loc[average_delivery_time['Czas trwania cyklu'].idxmax()]
    slowest_customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Najwolniej obsługiwany klient</h3><p>{slowest_customer['Nazwa klienta']}</p></div><div style='text-align: center;'><h3>Średni czas realizacji wysyłek (dni)</h3><p>{slowest_customer['Czas trwania cyklu']:.2f}</p></div></div>"
    fastest_customer = average_delivery_time.loc[average_delivery_time['Czas trwania cyklu'].idxmin()]
    fastest_customer_info = f"<div style='display:flex; justify-content: space-between;'><div style='text-align: center; padding-right: 10px;'><h3 style='word-wrap: break-word;'>Najszybciej obsługiwany klient</h3><p>{fastest_customer['Nazwa klienta']}</p></div><div style='text-align: center;'><h3>Średni czas realizacji wysyłek (dni) </h3><p>{fastest_customer['Czas trwania cyklu']:.2f}</p></div></div>"
    st.markdown(fastest_customer_info, unsafe_allow_html=True)
    st.markdown(slowest_customer_info, unsafe_allow_html=True)