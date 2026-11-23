CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id));
INSERT INTO customers VALUES (1, 'Lea'), (2, 'Mina'), (3, 'Dan');
INSERT INTO orders VALUES (11, 1), (12, 1), (13, 3), (14, NULL);
