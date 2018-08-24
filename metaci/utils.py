from django.utils.crypto import get_random_string

def is_attr_equal(o1, o2, attrs):
    """Compare two objects using a list of attributes."""
    for attr in attrs:
        if getattr(o1, attr) != getattr(o2, attr):
            return False
    return True

def generate_hash():
    return get_random_string(64)
