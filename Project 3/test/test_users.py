from TodoApp.routers.todos import get_db, get_current_user  # 👈 'get_current_user' ko routers se uthaya
from TodoApp.utils import *
from TodoApp.test.models import Todos
from fastapi import status
# 2. Test Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_todos.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Dependencies Override karne ke functions
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    # Aapke authenticated test cases isi user session ko use karenge
    return {"username": "Gauresh", "id": 2, "user_role": "admin"}

# Overrides apply kijiye
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_users(client):
    response = client.get("/users")
    assert response.status_code == 200
    assert response.json()[0]["username"] == "gauresh"
    assert response.json()[0]["email"] == "gauresh.19@gmail.com"
    assert response.json()[0]["first_name"] == "Gauresh"
    assert response.json()[0]["last_name"] == "dev"
    assert response.json()[0]["role"] == "admin"
    assert response.json()[0]["phone_number"] == "1234567890"

def test_change_password_success(client):
    response = client.put("/users/change-password", json={
        "old_password": "password",
        "new_password": "newpassword"
    })
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_change_password_failure(client):
    response = client.put("/users/change-password", json={
        "old_password": "wrongpassword",
        "new_password": "newpassword"
    })
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Old password is incorrect."}

def test_change_phone_number_success(client):
    response = client.put("/users/change-phone-number", json={
        "new_phone_number": "0987654321"
    })
    assert response.status_code == status.HTTP_204_NO_CONTENT

def test_change_phone_number_failure(client):
    response = client.put("/users/change-phone-number", json={
        "new_phone_number": "invalidnumber"
    })
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY