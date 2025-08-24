import random2

def generate_code():
    return ''.join([str(random2.randint(0, 9)) for _ in range(4)])
