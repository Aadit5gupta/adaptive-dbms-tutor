CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id));
INSERT INTO customers VALUES (2, 'Alex'), (3, 'Alex'), (4, 'Jo');
INSERT INTO orders VALUES (10, 2), (11, 2), (12, 3), (13, NULL);
