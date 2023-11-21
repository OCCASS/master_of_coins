def is_int(s: str) -> bool:
    try:
        _ = int(s)
        return True
    except ValueError:
        return False


def is_float(s: str) -> bool:
    try:
        _ = float(s)
        return True
    except ValueError:
        return False
