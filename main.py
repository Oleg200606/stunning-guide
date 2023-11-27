import sqlite3
import hashlib
import pickle
from oll import Item


conn = sqlite3.connect('shop.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
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

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_carts (
    user_id INTEGER PRIMARY KEY,
    cart_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (cart_id) REFERENCES carts(id)
)''')
               
cursor.execute('''
CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
)''')




class Category:
    def __init__(self, name):
        self.name = name

    def save_baze(self):
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (self.name,))
        conn.commit()

    @staticmethod
    def all_categori():
        cursor.execute('SELECT * FROM categories')
        return cursor.fetchall()

    @staticmethod
    def name_categori(name):
        cursor.execute('SELECT * FROM categories WHERE name=?', (name,))
        return cursor.fetchone()
    
class Cart:
    def __init__(self):
        self.items = {}

    def add_item(self, product, quantity):
        if product in self.items:
            self.items[product] += quantity
        else:
            self.items[product] = quantity

    def remove_item(self, product):
        if product in self.items:
            del self.items[product]

    

class Product(Item):
    def __init__(self, name, price, quantity):
        super().__init__(name, price, quantity)
        self.categories = [] 

    def save_baze(self):
        cursor.execute('INSERT INTO items (name, price, quantity) VALUES (?, ?, ?)',
                       (self.name, self.price, self.quantity))
        conn.commit()

        for category_id in self.categories:
            cursor.execute('INSERT INTO item_categories (item_id, category_id) VALUES (?, ?)',
                           (cursor.lastrowid, category_id))
            conn.commit()

    def add_category(self, category_id):
        self.categories.append(category_id)

    def name_prodykt(name):
        cursor.execute('SELECT * FROM items WHERE name=?', (name,))
        return cursor.fetchone()

    @staticmethod
    def all_prodykt():
        cursor.execute('SELECT items.*, GROUP_CONCAT(item_categories.category_id) AS category_ids FROM items LEFT JOIN item_categories ON items.id = item_categories.item_id GROUP BY items.id')
        return cursor.fetchall()

    def delete_baze(self):
        cursor.execute('DELETE FROM items WHERE name=?', (self.name,))
        conn.commit()

    def update_prodykt(self, new_name=None, new_price=None, new_quantity=None):
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
    def __init__(self, username, password, role):
        self.username = username
        self.password = self.hashe_password(password)
        self.role = role
        self.cart_id = None

    @staticmethod
    def hashe_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def save_baze(self):
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                           (self.username, self.password, self.role))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("Пользователь с таким именем уже существует")

    @staticmethod
    def auth(username, password):
        encrypted_password = User.hashe_password(password)
        cursor.execute('SELECT id, role FROM users WHERE username=? AND password=?',
                       (username, encrypted_password))
        user_data = cursor.fetchone()
        if user_data:
            user_id, role = user_data
            return user_id, role
        else:
            return None, None
        

class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def name_prodykt(self):
        return self.product.name
    

class Order(Item):
    def __init__(self, user_id, product_name, quantity):
        super().__init__(product_name, 0, quantity)
        self.user_id = user_id

    def save_baze(self):
        item = Product.name_prodykt(self.name)
        if item:
            cursor.execute('INSERT INTO orders (user_id, item_id, quantity) VALUES (?, ?, ?)',
                           (self.user_id, item[0], self.quantity))
            conn.commit()
        else:
            print("Товар не найден.")



def create_order(user_id):
    try:
        item_name = input("Введите название товара для заказа: ")
        item = Product.name_prodykt(item_name)
        if item:
            quantity = int(input("Введите количество товара для заказа: "))
            if item[3] >= quantity:
                if user_id not in user_carts:
                    user_carts[user_id] = Cart()

                user_cart = user_carts[user_id]
                prodykt = Product(item[1], item[2], item[3])
                user_cart.add_item(prodykt, quantity)

                print("Заказ успешно добавлен в корзину.")
                cursor.execute('UPDATE items SET quantity=quantity-? WHERE id=?', (quantity, item[0]))
                conn.commit()
            else:
                print("Недостаточно товара на складе.")
        else:
            print("Товар не найден.")
    except ValueError:
        print("Неверное количество товара.")

def del_prodykt():
    cursor.execute('DELETE FROM items WHERE quantity <= 0')
    conn.commit()

def register_user():
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    role = input("Введите роль (покупатель или продавец): ")
    if role.lower() not in ["покупатель", "продавец"]:
        print("Неверная роль. Пожалуйста, введите 'покупатель' или 'продавец'.")
        return

    try:
        new_user = User(username, password, role)
        new_user.save_baze()

        # Получите идентификатор пользователя из базы данных после сохранения
        cursor.execute('SELECT id FROM users WHERE username=?', (username,))
        user_id = cursor.fetchone()[0]

        # Создайте корзину для пользователя и установите связь между пользователем и корзиной
        cursor.execute('INSERT INTO carts (user_id) VALUES (?)', (user_id,))
        conn.commit()

        print("Пользователь успешно зарегистрирован.")
    except ValueError as e:
        print(e)


def login_user():
    username = input("Введите имя пользователя: ")
    password = input("Введите пароль: ")
    user_id, role = User.auth(username, password)
    if user_id is not None and role is not None:
        print(f"Вы успешно вошли в систему как {role}.")
        return user_id, role
    else:
        print("Неверное имя пользователя или пароль.")
        return None, None
    

def carta(user_id):
    if user_id in user_carts:
        cart = user_carts[user_id]
        if cart.items:
            print("Ваша корзина:")
            for item, quantity in cart.items.items():
                print(f"Товар: {item.name}, Количество: {quantity}")
        else:
            print("Ваша корзина пуста.")
    else:
        print("Корзина не найдена.")


def save_cart(user_id, cart):
    with open(f"user_{user_id}_cart.pkl", "wb") as file:
        pickle.dump(cart, file)
            
def load_cart(user_id):
    try:
        with open(f"user_{user_id}_cart.pkl", "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return Cart()
    

def del_carta(user_carts, user_id):
    if user_id in user_carts:
        user_cart = user_carts[user_id]
        product_name = input("Введите название товара для удаления из корзины: ")

        print("Содержимое вашей корзины:")
        for product, quantity in user_cart.items.items():
            print(f"Товар: {product.name}, Количество: {quantity}")

        found_product = None
        for product in user_cart.items:
            if product.name == product_name:
                found_product = product
                break

        if found_product:
            user_cart.remove_item(found_product)
            print(f"{product_name} успешно удален из вашей корзины.")
            
        else:
            print(f"{product_name} отсутствует в вашей корзине.")
    else:
        print("Корзsина не найдена.")

def proverka(prompt, data_type):
    while True:
        user_input = input(prompt)
        try:
            value = data_type(user_input)
            return value
        except ValueError:
            print("Пожалуйста, введите корректное числовое значение.")





user_carts = {}  

if __name__ == "__main__":
    while True:
        print("\n1. Регистрация")
        print("2. Авторизация")
        print("3. Выход")
        dei = input("Выберите действие: ")

        if dei == "1":
            register_user()
        elif dei == "2":
            user_id, role = login_user()
            if user_id is not None:
                if role == "покупатель":
                    if user_id not in user_carts:
                        user_cart = load_cart(user_id)
                        user_carts[user_id] = user_cart
                        while True:
                            print("\n1. Получение списка товаров")
                            print("2. Оформление заказа")
                            print("3. Просмотр корзины")
                            print("4. Удаление товара из корзины")
                            print("0. Выход и сохранение")
                            dei2 = input("Выберите действие: ")

                            if dei2 == "1":
                                items = Product.all_prodykt()
                                if items:
                                    print("Товары:")
                                    for item in items:
                                        print(f"ID: {item[0]}, Название: {item[1]}, Цена: {item[2]}, Количество: {item[3]}, Категории: {item[4]}")
                                else:
                                    print("Список товаров пуст.")
                            if dei2 == "2":
                                item_name = input("Введите название товара для заказа: ")
                                item = Product.name_prodykt(item_name)
                                if item:
                                    quantity = proverka("Введите количество товара для заказа: ", int)  
                                    if item[3] >= quantity:
                                        prodykt = Product(item[1], item[2], item[3])  
                                        user_cart.add_item(prodykt, quantity)  
                                        print("Заказ успешно добавлен в корзину.")
                                        cursor.execute('UPDATE items SET quantity=quantity-? WHERE id=?', (quantity, item[0]))
                                        conn.commit()
                                    else:
                                        print("Недостаточно товара на складе.")
                                else:
                                    print("Товар не найден.")

                            elif dei2 == "3":
                                carta(user_id)
                            elif dei2 == "4":
                                del_carta(user_carts, user_id)

                                
                            elif dei2 == "0":
                                save_cart(user_id, user_cart)
                                del_prodykt()
                                
                                break
                elif role == "продавец":
                        while True:
                            print("\n1. Добавить товар")
                            print("2. Получение списка товаров")
                            print("3. Обновление товара")
                            print("4. Удаление товара")
                            print("5. Добавить категорию")
                            print("6. Получение списка категорий")
                            print("0. Выход и сохранение")
                            dei2 = input("Выберите действие: ")

                            if dei2 == "1":
                                nam = input("Введите название товара: ")
                                zhen = proverka("Введите цену товара: ", float)
                                kol_vo = proverka("Введите количество товара: ", int)          
                                new_product = Product(nam, zhen, kol_vo)
                                new_product.save_baze()
                                print("Товар успешно добавлен.")

                                categories = input("Введите категории товара через запятую: ")
                                if categories:
                                    categories = categories.split(',')
                                    for category in categories:
                                        category = category.strip()
                                        categor = Category.name_categori(category)
                                        if categor:
                                            new_product.add_category(categor[0])
                                        else:
                                            print(f"Категория '{category}' не найдена и не будет привязана к товару.")

                            elif dei2 == "2":
                                items = Product.all_prodykt()
                                if items:
                                    print("Товары:")
                                    for item in items:

                                        print(f"ID: {item[0]}, Название: {item[1]}, Цена: {item[2]}, Количество: {item[3]}, Категории: {item[4]}")
                                else:
                                    print("Список товаров пуст.")

                            elif dei2 == "3":
                                name_update = input("Введите название товара для обновления: ")
                                exist = Product.name_prodykt(name_update)
                                if exist:
                                    existing = Product(exist[1], exist[2], exist[3])
                                    new_name = input("Введите новое название товара: ")
                                    new_price = proverka("Введите новую цену товара: ", float) 
                                    new_quantity = proverka("Введите новое количество товара: ", int) 
                                    existing.update_prodykt(new_name, new_price, new_quantity)
                                    print("Товар успешно обновлен.")
                                else:
                                    print("Товар не найден.")

                            elif dei2 == "4":
                                name_to_delete = input("Введите название товара для удаления: ")
                                exist = Product.name_prodykt(name_to_delete)
                                if exist:
                                    existing = Product(exist[1], exist[2], exist[3])
                                    existing.delete_baze()
                                    print("Товар успешно удален.")
                                else:
                                    print("Товар не найден.")

                            elif dei2 == "5":
                                category_name = input("Введите название категории: ")
                                new_category = Category(category_name)
                                new_category.save_baze()
                                print("Категория успешно добавлена.")

                            elif dei2 == "6":
                                categories = Category.all_categori()
                                if categories:
                                    print("Категории:")
                                    for category in categories:
                                        print(f"ID: {category[0]}, Название: {category[1]}")
                                else:
                                    print("Список категорий пуст.")

                            elif dei2 == "0":
                                break
        elif dei == "3":
            conn.close()
            break
conn.close()