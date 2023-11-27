class Item:
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

    def save_baze(self):
        raise NotImplementedError("Подклассы должны реализовывать метод save_baze")
