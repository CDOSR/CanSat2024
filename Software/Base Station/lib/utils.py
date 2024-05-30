import machine

def get_random_byte():
    return machine.rng()  # Note: This only works if your hardware supports it

def generate_random_filename():
    # Generate a list of 10 characters by alternating between random letters and numbers
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz'
    filename = ''.join(chars[get_random_byte() % len(chars)] for _ in range(10)) + '.txt'
    return filename