def stats_cart(cart_items):
    return {
        'total_quantity': len(cart_items) if cart_items else 0
    }

def can_borrow(currently_borrowed, in_cart_count, limit=5):
    return (currently_borrowed + in_cart_count) < limit

def is_over_limit(currently_borrowed, in_cart_count, limit=5):
    return (currently_borrowed + in_cart_count) > limit

