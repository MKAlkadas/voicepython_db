import sqlite3
import os

class DBService:
    def __init__(self, db_path="products.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_product(self, name, price, description=""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, price, description) VALUES (?, ?, ?)', (name, price, description))
        conn.commit()
        conn.close()

    def get_product_by_name(self, name):
        """
        Simple search for a product by name.
        Returns the first matching product or None.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Using LIKE for simple partial matching
        cursor.execute('SELECT * FROM products WHERE name LIKE ?', (f'%{name}%',))
        product = cursor.fetchone()
        conn.close()
        if product:
            return {
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "description": product[3]
            }
        return None

    def get_all_products(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products')
        rows = cursor.fetchall()
        conn.close()
        products = []
        for row in rows:
            products.append({
                "id": row[0],
                "name": row[1],
                "price": row[2],
                "description": row[3]
            })
        return products

    def seed_data(self):
        """Add some sample products if the table is empty."""
        if not self.get_all_products():
            products = [
                ("iPhone 15", 3500.0, "Latest Apple smartphone"),
                ("Samsung S24", 3200.0, "Samsung flagship phone"),
                ("MacBook Pro", 8000.0, "Apple laptop M3 chip"),
                ("Dell XPS", 6500.0, "High performance Windows laptop"),
                ("AirPods Pro", 900.0, "Wireless noise cancelling earbuds"),
                ("ايفون 15", 3500.0, "أحدث هاتف من آبل"),
                ("سامسونج اس 24", 3200.0, "هاتف سامسونج الرائد"),
                ("لابتوب ديل", 4500.0, "كمبيوتر محمول للأعمال")
            ]
            for p in products:
                self.add_product(p[0], p[1], p[2])
            print("Database seeded with sample products.")
