class DatabaseError(Exception):
    pass


class Storage:
    def __init__(self, connection):
        self.connection = connection

    def transaction(self):
        return self.connection.transaction()

    def save_order(self, order):
        try:
            self.connection.execute(
                "insert into orders (id, amount) values (?, ?)",
                (order["id"], order["amount"]),
            )
            self.connection.commit()
            return True
        except DatabaseError:
            return False
