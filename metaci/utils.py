import itertools

from django.utils.crypto import get_random_string


def is_attr_equal(o1, o2, attrs):
    """Compare two objects using a list of attributes."""
    for attr in attrs:
        if getattr(o1, attr) != getattr(o2, attr):
            return False
    return True


def generate_hash():
    return get_random_string(64)


# from https://stackoverflow.com/a/3226719/11151197
def split_seq(iterable, size):
    """Split an iterable into batches of a particular size.
    The last batch may be smaller."""
    it = iter(iterable)
    item = list(itertools.islice(it, size))
    while item:
        yield item
        item = list(itertools.islice(it, size))
