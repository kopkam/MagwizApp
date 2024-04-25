import streamlit as st
from st_pages import Page, show_pages, add_page_title


def main():
    left_co, cent_co, cent_co2, last_co = st.columns(4)
    with cent_co:
        st.image(r'C:\Users\marcin\Magwiz\MAGWIZ.png', width=350)
    st.markdown("<h1 style='text-align: center; color: black;'>Skutecznie zarządzaj zapasami w magazynie</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.write(
        """
        Prosta w obsłudze aplikacja Magwiz to narzędzie usprawniające przepływ zapasów
        w magazynie. Wszystkie niezbędne funkcje w jednym miejscu! 
        """
    )
    # Opis funkcji
    st.header('Funkcje:')
    st.markdown("""
    - **Eksploracja Danych (🔍):** Aktualizuj i przeglądaj dane związane z działalnością magazynową, aby lepiej zrozumieć trendy i wzorce.
    - **Stany Zapasów (📦):** Śledź aktualne stany zapasów produktów oraz monitoruj ich zmiany w czasie.
    - **Braki Magazynowe (⚠️):** Otrzymuj informację o brakach magazynowych i podejmuj odpowiednie działania w celu ich rozwiązania.
    - **Analiza ABC (📊):** Analizuj produkty pod kątem ich wartości i znaczenia dla działalności, aby lepiej zarządzać zapasami.
    - **Terminowość zamówień (🚚):** Monitoruj terminowość dostaw oraz wysyłek oraz identyfikuj opóźnienia w celu optymalizacji procesów logistycznych.
    - **Czas realizacji zamówień(⏱️):** Monitoruj czas, jaki zajmuje realizacja dostaw oraz zamówień, aby zapewnić terminowe dostawy i optymalizować procesy logistyczne.
    - **Procent Wypełnienia Magazynu (📈):** Sprawdzaj stopień wypełnienia magazynu i podejmuj decyzje dotyczące jego optymalnego wykorzystania.
    """)

    st.write("Proszę wybrać jedną z opcji z panelu po lewej stronie.")

    show_pages(
        [
            Page("main.py", "Strona główna", "🏠"),
            Page("pages/1_eksploracja_danych.py", "Eksploracja danych", "🔍"),
            Page("pages/2_stany_zapasow.py", "Stany zapasów", "📦"),
            Page("pages/3_braki_magazynowe.py", "Braki magazynowe", "⚠️"),
            Page("pages/4_analiza_abc.py", "Analiza ABC", "📊"),
            Page("pages/5_terminowosc_dostaw.py", "Terminowość zamówień", "🚚"),
            Page("pages/6_realizacja_dostaw.py", "Czas realizacji zamówień", "⏱️"),
            Page("pages/7_wypelnienie_magazynow.py", "Wypełnienie magazynów", "📈")

        ]
    )

if __name__ == "__main__":
    main()
