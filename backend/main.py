try:
    from app.factory import create_app
except ModuleNotFoundError as exc:
    if exc.name != "app":
        raise
    from backend.app.factory import create_app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
