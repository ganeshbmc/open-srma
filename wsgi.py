from app import app


if __name__ == "__main__":
    # Fallback for running directly, though production should use a WSGI server
    app.run()

