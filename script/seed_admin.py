from pathlib import Path
from app.db import init_db, one, execute
from app.security import hash_password

CREDENTIAL_FILE = Path('/opt/vexora/first-login')


def main() -> None:
    init_db()
    if one('SELECT id FROM admins LIMIT 1') is not None:
        return
    if not CREDENTIAL_FILE.exists():
        return
    values = {}
    for line in CREDENTIAL_FILE.read_text(encoding='utf-8').splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            values[key] = value
    username = values.get('USERNAME')
    password = values.get('PASSWORD')
    if not username or not password:
        raise SystemExit('Invalid first-login credential file')
    execute(
        'INSERT INTO admins(username,password_hash,role) VALUES(?,?,?)',
        (username, hash_password(password), 'owner'),
    )
    CREDENTIAL_FILE.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
