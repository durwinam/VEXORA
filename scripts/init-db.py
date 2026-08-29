from app.database import health_check, initialize


initialize()


if not health_check():
    raise SystemExit(
        "Database health check failed."
    )


print("Database initialized successfully.")
