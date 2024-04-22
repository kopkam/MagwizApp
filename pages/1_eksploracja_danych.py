import streamlit as st
import pandas as pd
import sqlite3
import os

# Funkcja do pobierania nazw istniejących tabel z bazy danych
def get_table_names(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    return [table[0] for table in tables]

# Funkcja do pobierania pierwszych i ostatnich rekordów z wybranej tabeli
def get_first_last_records(conn, table_name):
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)

    return df

# Funkcja do usuwania duplikatów w pierwszej kolumnie tabeli
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

# Funkcja do aktualizacji danych z plików Excel
def update_data(conn):
    folder_path = 'Dane'
    excel_files = {
        'Dostawcy.xlsx': 'Dostawcy',
        'Produkty.xlsx': 'Produkty',
        'Magazyny.xlsx': 'Magazyny',
        'StanyMagazynowe.xlsx': 'StanyMagazynowe',
        'Klienci.xlsx': 'Klienci',
        'Zamówienia.xlsx': 'Zamowienia',
        'ZamówieniaSzczegóły.xlsx': 'ZamowieniaSzczegoly',
        'Dostawy.xlsx': 'Dostawy',
        'DostawySzczegóły.xlsx': 'DostawySzczegoly'
    }

    for excel_file, table_name in excel_files.items():
        excel_path = os.path.join(folder_path, excel_file)
        if os.path.exists(excel_path):
            existing_data = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            new_data = pd.read_excel(excel_path)
            
            # Usuwamy duplikaty w pierwszej kolumnie
            num_duplicates_removed = remove_duplicates(conn, table_name)
            if num_duplicates_removed > 0:
                st.write(f"Usunięto {num_duplicates_removed} duplikatów w tabeli '{table_name}'.")
            
            # Dodajemy nowe rekordy
            new_records = new_data[~new_data.iloc[:, 0].isin(existing_data.iloc[:, 0])]
            num_added_records = len(new_records)
            new_records.to_sql(table_name, conn, if_exists='append', index=False)
            st.write(f"Do tabeli '{table_name}' dodano {num_added_records} nowych rekordów.")
            
            # Usuwamy rekordy, które nie istnieją w pliku Excel, ale istnieją w bazie danych
            records_to_delete = existing_data[~existing_data.iloc[:, 0].isin(new_data.iloc[:, 0])]
            num_deleted_records = len(records_to_delete)
            if num_deleted_records > 0:
                for index, row in records_to_delete.iterrows():
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {table_name} WHERE {existing_data.columns[0]} = ?", (row[existing_data.columns[0]],))
                    conn.commit()
                st.write(f"Z tabeli '{table_name}' usunięto {num_deleted_records} rekordów.")
        else:
            st.write(f"Plik '{excel_file}' nie istnieje. Pomijanie...")

# Połączenie z bazą danych SQLite
conn = sqlite3.connect('DB_ZAPASY.db')

# Strona Streamlit
def main():
    st.title('Aktualizacja danych pochodzących z plików Excel')

    # Przycisk do aktualizacji plików
    update_button = st.button("Aktualizuj dane")
    st.markdown('---')

    if update_button:
        messages_to_clear = st.empty()  # Przechowujemy stan komunikatów
        update_data(conn)
        st.write("Aktualizacja zakończona.")
        # Wyświetl przycisk do wyczyszczenia komunikatów tylko jeśli wykonano aktualizację
        st.button("Wyczyść")

    st.title('Wyświetlanie nazw dostępnych plików')
    st.markdown('---')
    
    # Przyciski do wyświetlenia/ukrycia tabel
    show_files = st.button('Pokaż pliki')
    hide_files = False

    if show_files:
        table_names = get_table_names(conn)
        if table_names:
            st.write("Dostępne pliki:")
            for table_name in table_names:
                st.write(f"- {table_name}")
        else:
            st.write("Brak plików.")
        hide_files = st.button('Ukryj pliki')

    if hide_files:
        st.text("Pliki ukryte.")

    st.title('Wyświetlanie zawartości plików')

    table_names = get_table_names(conn)
    selected_table = st.selectbox('Wybierz dostęny plik', table_names)
    st.write(f"Wybrany plik: {selected_table}")

    show_records = st.button('Pokaż zawartość')
    hide_records = False

    if show_records:
        df = get_first_last_records(conn, selected_table)
        st.write("Aktualne dane:")
        st.dataframe(df, hide_index=True)
        hide_records = st.button('Ukryj zawartość')

    if hide_records:
        st.text("Zawartość ukryta.")

if __name__ == "__main__":
    main()
