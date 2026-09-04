def persist_order(storage, order):
    with storage.transaction():
        for _ in range(3):
            if storage.save_order(order):
                return True
    return False
