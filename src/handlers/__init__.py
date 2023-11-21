def register_all():
    for module in (
        "admin",
        "users",
    ):
        __import__(f"src.handlers.{module}")
