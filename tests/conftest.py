import pytest

from main import create_app
from main.db import db
from main.auth import encode_jwt
from tests import TEST_USERNAME, TEST_PASSWORD, TEST_UNAUTH_USER
from tests.helpers import initialize_test_data, login


@pytest.fixture(scope='session')
def app():
    app = create_app()
    db.init_app(app)
    with app.app_context():
        db.drop_all()
        db.create_all()
        initialize_test_data()
        yield app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def runner(app):
    return app.test_cli_runner()


@pytest.fixture(scope='module')
def access_token():
    token = encode_jwt(1).decode('UTF-8')
    return token


@pytest.fixture(scope='module')
def unauth_token():
    token = encode_jwt(2).decode('UTF-8')
    return token
