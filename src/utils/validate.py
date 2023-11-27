def is_float(s: str) -> bool:
    try:
        _ = float(s)
        return True
    except ValueError:
        return False
