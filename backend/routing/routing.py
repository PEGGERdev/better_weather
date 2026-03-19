try:
    from app.factory import create_app
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from backend.app.factory import create_app

__all__ = ["create_app"]
