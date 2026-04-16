def stats_cart(cart):

    total_quantity = 0
    if cart:

        total_quantity = len(cart)

    return {
        'total_quantity': total_quantity
    }


def check_borrow_limit(currently_borrowed_count, in_cart_count, limit=5):

    return (currently_borrowed_count + in_cart_count) < limit


def get_total_potential_borrow(currently_borrowed_count, in_cart_count):

    return currently_borrowed_count + in_cart_count