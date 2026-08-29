# Security checklist

- Admin session cookie is HttpOnly.
- SameSite is set to Lax.
- Secure is enabled for the production HTTPS cookie.
- Passwords are stored as PBKDF2-SHA256 hashes rather than plaintext.
- The generated `.env` is mode 0600.
- Installation credentials are written to a mode 0600 installation report.
- Administrator login failures are recorded in the audit log.
- Order, plan, server, support and settings mutations are recorded.
- SQLite foreign keys are enabled.
- SQLite uses WAL mode and a non-zero connection timeout.
- Nginx limits request body size.
- Static files are served directly by Nginx.
- Backend listens on 0.0.0.0 as requested, while public application access
  is intended to pass through the TLS proxy.
- The installer does not create fake certificates.
- The installer does not declare success if the backend health check fails.
- The installer does not declare success if the public TLS route fails.
