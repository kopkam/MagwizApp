USE DB_ZAPASY;

CREATE TABLE Dostawcy (
    id_dostawca INT IDENTITY(1,1) PRIMARY KEY,
    nazwa_dostawcy VARCHAR(255) NOT NULL
);

CREATE TABLE Produkty (
    kod_produktu INT IDENTITY(1,1) PRIMARY KEY,
    nazwa_produktu VARCHAR(255) NOT NULL,
    kategoria VARCHAR(255),
    zapas_bezpieczenstwa INT,
	ilosc_szt_w_opk_zbiorczym INT,
	objetosc_sztuki DECIMAL(5, 2),
	wymiar_wysokosc INT,
	wymiar_szerokosc INT,
	wymiar_glebokosc INT,
	wymiar_masa INT
    -- inne atrybuty produktów...
);

CREATE TABLE Magazyny (
    id_magazynu INT IDENTITY(1,1) PRIMARY KEY,
    nazwa_magazynu VARCHAR(255) NOT NULL
    -- inne atrybuty magazynów...
);

CREATE TABLE StanyMagazynowe (
    id_stan INT IDENTITY(1,1) PRIMARY KEY,
    kod_produktu INT,
    id_magazynu INT,
    ilosc_na_stanie INT,
    ilosc_dostepna INT,
    ilosc_zarezerwowana INT,
    -- inne atrybuty stanów magazynowych...
    FOREIGN KEY (kod_produktu) REFERENCES Produkty(kod_produktu),
    FOREIGN KEY (id_magazynu) REFERENCES Magazyny(id_magazynu)
);

CREATE TABLE Klienci (
    id_klient INT IDENTITY(1,1) PRIMARY KEY,
    nazwa_klienta VARCHAR(255) NOT NULL
);

CREATE TABLE Zamowienia (
    id_zamowienia INT IDENTITY(1,1) PRIMARY KEY,
    id_klient INT,
    data_zamowienia DATE,
    oczekiwany_termin_wysylki DATE,
    data_wysylki DATE,
    status VARCHAR(255),
    kanal_sprzedazy VARCHAR(255),
    -- inne atrybuty zamówień...
    FOREIGN KEY (id_klient) REFERENCES Klienci(id_klient)
);

CREATE TABLE ZamowieniaSzczegoly (
    zamowienie_produkt_id INT IDENTITY(1,1) PRIMARY KEY,
    id_zamowienia INT,
    kod_produktu INT,
    ilosc INT,
    -- inne atrybuty szczegółów zamówienia...
    FOREIGN KEY (id_zamowienia) REFERENCES Zamowienia(id_zamowienia),
    FOREIGN KEY (kod_produktu) REFERENCES Produkty(kod_produktu)
);

CREATE TABLE Dostawy (
    id_dostawy INT IDENTITY(1,1) PRIMARY KEY,
    id_dostawca INT,
    data_zamowienia DATE,
    oczekiwana_data_dostawy DATE,
    data_dostawy DATE,
    status VARCHAR(255),
    -- inne atrybuty dostaw...
    FOREIGN KEY (id_dostawca) REFERENCES Dostawcy(id_dostawca)
);

CREATE TABLE DostawySzczegoly (
    id_szczegol_dostawy INT IDENTITY(1,1) PRIMARY KEY,
    id_dostawy INT,
    kod_produktu INT,
    ilosc INT,
    -- inne atrybuty szczegółów dostawy...
    FOREIGN KEY (id_dostawy) REFERENCES Dostawy(id_dostawy),
    FOREIGN KEY (kod_produktu) REFERENCES Produkty(kod_produktu)
);
