<<<<<<< HEAD
﻿USE DB_INVENTORY;

CREATE TABLE Suppliers (
    supplier_id INT IDENTITY(1,1) PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL
);

CREATE TABLE Products (
    product_code INT IDENTITY(1,1) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(255),
    safety_stock INT,
    units_per_package INT,
    unit_volume DECIMAL(5, 2),
    unit_height INT,
    unit_width INT,
    unit_depth INT,
    unit_weight INT
);

CREATE TABLE Warehouses (
    warehouse_id INT IDENTITY(1,1) PRIMARY KEY,
    warehouse_name VARCHAR(255) NOT NULL,
    capacity INT
);

CREATE TABLE WarehouseStock (
    stock_id INT IDENTITY(1,1) PRIMARY KEY,
    stock_date DATE,
    product_code INT,
    warehouse_id INT,
    quantity_on_hand INT,
    quantity_reserved INT,
    quantity_available INT,
    FOREIGN KEY (product_code) REFERENCES Products(product_code),
    FOREIGN KEY (warehouse_id) REFERENCES Warehouses(warehouse_id)
);

CREATE TABLE Customers (
    customer_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL
);

CREATE TABLE Orders (
    order_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT,
    order_date DATE,
    expected_shipping_date DATE,
    shipping_date DATE,
    shipping_status VARCHAR(255),
    sales_channel VARCHAR(255),
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

CREATE TABLE OrderDetails (
    order_product_id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT,
    product_code INT,
    quantity INT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id),
    FOREIGN KEY (product_code) REFERENCES Products(product_code)
);

CREATE TABLE Deliveries (
    delivery_id INT IDENTITY(1,1) PRIMARY KEY,
    supplier_id INT,
    order_date DATE,
    expected_delivery_date DATE,
    delivery_date DATE,
    delivery_status VARCHAR(255),
    -- other delivery attributes...
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
);

CREATE TABLE DeliveryDetails (
    delivery_detail_id INT IDENTITY(1,1) PRIMARY KEY,
    delivery_id INT,
    product_code INT,
    quantity INT,
    FOREIGN KEY (delivery_id) REFERENCES Deliveries(delivery_id),
    FOREIGN KEY (product_code) REFERENCES Products(product_code)
);
=======
﻿USE DB_ZAPASY;

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
    id_magazyn INT IDENTITY(1,1) PRIMARY KEY,
    nazwa_magazynu VARCHAR(255) NOT NULL,
    pojemnosc INT
);

CREATE TABLE StanyMagazynowe (
    id_stan INT IDENTITY(1,1) PRIMARY KEY,
    data_stanu DATE,
    kod_produktu INT,
    id_magazyn INT,
    ilosc_na_stanie INT,
    ilosc_zarezerwowana INT,
    ilosc_dostepna INT,
    -- inne atrybuty stanów magazynowych...
    FOREIGN KEY (kod_produktu) REFERENCES Produkty(kod_produktu),
    FOREIGN KEY (id_magazyn) REFERENCES Magazyny(id_magazyn)
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
    status_wysylki VARCHAR(255),
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
    status_dostawy VARCHAR(255),
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
>>>>>>> origin/main
