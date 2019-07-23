import random
import string


def generate(amount: int) -> list:
    licenses = []
    for i in range(amount):
        licenses.append(generate_single())
    return licenses


def generate_single() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=30))
