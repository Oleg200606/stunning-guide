import sqlite3
import hashlib
from oll import Item 

conn = sqlite3.connect('shop.db')
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS item_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
)''')





class Category(Item):
    def __init__(self, name):
        super().__init__(name, 0, 0)  

    def save_to_db(self):
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (self.name,))
        conn.commit()

    @staticmethod
    def get_all_categories():
        cursor.execute('SELECT * FROM categories')
        return cursor.fetchall()
    
    @staticmethod
    def find_category_by_name(name):
        cursor.execute('SELECT * FROM categories WHERE name=?', (name,))
        return cursor.fetchone()


class Product(Item):
    def __init__(self, name, price, quantity):
        super().__init__(name, price, quantity)
        self.categories = []  

    def save_to_db(self):
        cursor.execute('INSERT INTO items (name, price, quantity) VALUES (?, ?, ?)',
                       (self.name, self.price, self.quantity))
        conn.commit()
        
        
        for category_id in self.categories:
            cursor.execute('INSERT INTO item_categories (item_id, category_id) VALUES (?, ?)',
                           (cursor.lastrowid, category_id))
            conn.commit()

    def add_category(self, category_id):
        self.categories.append(category_id)

    @staticmethod
    def get_all_products():
        cursor.execute('SELECT items.*, GROUP_CONCAT(item_categories.category_id) AS category_ids FROM items LEFT JOIN item_categories ON items.id = item_categories.item_id GROUP BY items.id')
        return cursor.fetchall()
    
    @staticmethod
    def find_product_by_name(name):
        cursor.execute('SELECT items.*, GROUP_CONCAT(item_categories.category_id) AS category_ids FROM items LEFT JOIN item_categories ON items.id = item_categories.item_id WHERE items.name=? GROUP BY items.id', (name,))
        return cursor.fetchone()

    def delete_from_db(self):
        cursor.execute('DELETE FROM items WHERE name=?', (self.name,))
        conn.commit()

    def update_product(self, new_name=None, new_price=None, new_quantity=None):
        if new_name:
            cursor.execute('UPDATE items SET name=? WHERE name=?', (new_name, self.name))
            self.name = new_name
        if new_price:
            cursor.execute('UPDATE items SET price=? WHERE name=?', (new_price, self.name))
            self.price = new_price
        if new_quantity:
            cursor.execute('UPDATE items SET quantity=? WHERE name=?', (new_quantity, self.name))
            self.quantity = new_quantity

        conn.commit()




class User:
    def __init__(self, username, password):
        self.username = username
        self.password = self._encrypt_password(password)

    @staticmethod
    def _encrypt_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def save_to_db(self):
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                           (self.username, self.password))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Пользователь с таким именем уже существует")

    @staticmethod
    def authenticate(username, password):
        encrypted_password = User._encrypt_password(password)
        cursor.execute('SELECT * FROM users WHERE username=? AND password=?',
                       (username, encrypted_password))
        return cursor.fetchone()


def register_user():
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    try:
        new_user = User(username, password)
        new_user.save_to_db()
        print("Пользователь успешно зарегистрирован.")
    except ValueError as e:
        print(e)

def login_user():
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    user = User.authenticate(username, password)
    if user:
        print("Вы успешно вошли в систему.")
        return user
    else:
        print("Неверное имя пользователя или пароль.")


if __name__ == "__main__":
    while True:
        print("\n1. Регистрация")
        print("2. Авторизация")
        print("3. Выход")
        choice = input("Выберите действие: ")

        if choice == "1":
            register_user()
        elif choice == "2":
            user = login_user()
            while user:
                print("\n1. Добавить товар")
                print("2. Получение списка товаров")
                print("3. Обновление товара")
                print("4. Удаление товара")
                print("5. Добавить категорию")
                print("6. Получение списка категорий")
                print("0. Выход и сохранение")
                action = input("Выберите действие: ")

                if action == "1":
                    nam = input("Введите название товара: ")
                    zhen = float(input("Введите цену товара: "))
                    kol_vo = int(input("Введите количество товара: "))
                    new_product = Product(nam, zhen, kol_vo)
                    new_product.save_to_db()
                    print("Товар успешно добавлен.")

                    categories = input("Введите категории товара через запятую: ")
                    if categories:
                        categories = categories.split(',')
                        for category in categories:
                            category = category.strip()
                            category_obj = Category.find_category_by_name(category)
                            if category_obj:
                                new_product.add_category(category_obj[0])
                            else:
                                print(f"Категория '{category}' не найдена и не будет привязана к товару.")

                elif action == "2":
                    items = Product.get_all_products()
                    if items:
                        print("Товары:")
                        for item in items:
                            print(f"ID: {item[0]}, Название: {item[1]}, Цена: {item[2]}, Количество: {item[3]}, Категории: {item[4]}")
                    else:
                        print("Список товаров пуст.")

                elif action == "3":
                    if items:
                        name_to_update = input("Введите название товара для обновления: ")
                        existing_item = Product.find_product_by_name(name_to_update)
                        if existing_item:
                            existing_item_obj = Product(existing_item[1], existing_item[2], existing_item[3])
                            new_name = input("Введите новое название товара: ")
                            new_price = float(input("Введите новую цену товара: "))
                            new_quantity = int(input("Введите новое количество товара: "))
                            existing_item_obj.update_product(new_name, new_price, new_quantity)
                            print("Товар успешно обновлен.")
                        else:
                            print("Товар не найден.")
                    else:
                        print("Список товаров пуст.")

                elif action == "4":
                    if items:
                        name_to_delete = input("Введите название товара для удаления: ")
                        existing_item = Product.find_product_by_name(name_to_delete)
                        if existing_item:
                            existing_item_obj = Product(existing_item[1], existing_item[2], existing_item[3])
                            existing_item_obj.delete_from_db()
                            print("Товар успешно удален.")
                        else:
                            print("Товар не найден.")
                    else:
                        print("Список товаров пуст.")

                elif action == "5":
                    category_name = input("Введите название категории: ")
                    new_category = Category(category_name)
                    new_category.save_to_db()
                    print("Категория успешно добавлена.")

                elif action == "6":
                    categories = Category.get_all_categories()
                    if categories:
                        print("Категории:")
                        for category in categories:
                            print(f"ID: {category[0]}, Название: {category[1]}")
                    else:
                        print("Список категорий пуст.")

                elif action == "0":
                    conn.close()
                    exit()

        elif choice == "3":
            conn.close()
            break
