
def calculate_total(price, quantity):
    return price + quantity  # Intentional bug


def calculate_discount(price, discount):
    return price - discount


if __name__ == "__main__":
    assert calculate_total(10, 3) == 30
    print("PASS")
