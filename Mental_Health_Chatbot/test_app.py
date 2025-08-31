import pytest # type: ignore
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.data

def test_login_get(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Username" in response.data

def test_login_invalid(client):
    response = client.post('/login',data={
        'username':'wrongname',
        'password':'wrongpassword'
    },follow_redirects = True)
    assert b"Invalid Credentials" in response.data

def teat_login_success(client):
    response = client.post('/login',data={
        'username':'Vaishnavi D',
        'password':'Vaishu&samu'
    })
    assert b"/Dashboard" in response.header['Location']

def test_register(client):
    response = client.get('/register')
    assert response.status_code == 200
    assert b"Username" in response.data

def test_register_usererror(client):
    response = client.post('/register',data={
        'username':'Vaishnavi D',
        'password':'wrongpassword'
    }, follow_redirect = True)
    assert b"Username" in response.data

