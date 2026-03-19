try:
    from main import app, create_app
except ModuleNotFoundError as exc:
    if exc.name != "main":
        raise
    from backend.main import app, create_app

__all__ = ["app", "create_app"]
