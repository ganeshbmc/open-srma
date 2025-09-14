import os
from app import app


def _bool_env(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).lower() in ("1", "true", "yes", "on")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    debug = _bool_env("FLASK_DEBUG", False) or os.environ.get("FLASK_ENV") == "development"
    app.run(host=host, port=port, debug=debug)
