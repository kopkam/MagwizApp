USE DB_INVENTORY;

CREATE TABLE Suppliers (
    supplier_id INT IDENTITY(1,1) PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL
);

CREATE TABLE Products (
    product_code INT IDENTITY(1,1) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    safety_stock INT,
    unit_height INT,
    unit_width INT,
    unit_depth INT,
    unit_volume DECIMAL(5, 2)
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