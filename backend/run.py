import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    host = app.config.get("FLASK_HOST", "127.0.0.1")
    port = app.config.get("FLASK_PORT", 5000)
    debug = app.config.get("DEBUG", False)

    print(f"\n==================================================")
    print(f" Queueless Smart Hospital API Server")
    print(f" Running at: http://{host}:{port}")
    print(f" Health check: http://{host}:{port}/api/v1/health")
    print(f"==================================================\n")

    app.run(host=host, port=port, debug=debug)
