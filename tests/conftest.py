import re

import pytest
from cryptography.fernet import Fernet

from registro import create_app
from registro.auth import crear_usuario
from registro.db import init_db


@pytest.fixture
def app(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "NHC_KEY": Fernet.generate_key().decode(),
        "HMAC_KEY": "clave-hmac-test",
        "DATABASE": str(tmp_path / "test.sqlite3"),
        "OUTBOX": str(tmp_path / "outbox"),
        "BASE_URL": "https://registro.test",
    })
    with app.app_context():
        init_db()
        crear_usuario("Admin", "admin@test.es", "contraseña-admin", True)
        crear_usuario("Dra. Uno", "uno@test.es", "contraseña-uno")
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def token(client, url="/login"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


@pytest.fixture
def login(client):
    def _login(email="admin@test.es", password="contraseña-admin"):
        t = token(client)
        client.post("/login", data={"email": email, "password": password, "csrf_token": t})
        return token(client, "/perfil")
    return _login
