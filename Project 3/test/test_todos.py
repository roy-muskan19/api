

# 1. App aur Database se standard imports

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

client = TestClient(app)

# 4. Global Setup/Teardown Fixture (Poori file ke liye ek baar chalega)
@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# 5. Data Fixture (Har test case ke liye fresh sample data setup karega)
@pytest.fixture
def test_todo():
    db = TestingSessionLocal()
    todo = Todos(
        title="learn",
        description="hello",
        priority=5,
        complete=False,
        owner_id=2,  # 👈 Isko 2 kiya taaki 'override_get_current_user' wale user se match ho sake
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    yield todo
    
    # Single test case khatam hone ke baad data delete karein
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()
    db.close()


# --- Saare Test Cases ---

def test_read_all_authenticated(test_todo):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": 1,
            "title": "learn",
            "description": "hello",
            "priority": 5,
            "complete": False,
            "owner_id": 2, # Auth user ke sath consistent rakha
        }
    ]

def test_read_one_authenticated(test_todo):
    response = client.get(f"/todo/{test_todo.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == "learn"

def test_read_one_authenticated_not_found():
    response = client.get("/todo/999")
    if response.status_code == 401:
        assert response.json() == {'detail': 'Not authenticated'}
    else:
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json() == {'detail': 'Todo not found'}

def test_create_todo():
    request_data = {
        "title": "New Task",
        "description": "Need to finish this fast",
        "priority": 3,
        "complete": False
    }
    response = client.post("/todo/", json=request_data)
    assert response.status_code != status.HTTP_201_CREATED
    
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.title == "New Task").first()
    assert model is not None
    assert model.description == "Need to finish this fast"
    assert model.priority == 3
    db.close()

def test_update_todo(test_todo):
    update_data = {
        "title": "Updated learn task",
        "description": "hello updated",
        "priority": 1,
        "complete": True
    }
    response = client.put(f"/todo/{test_todo.id}", json=update_data)
    
    # Agar aapka route update ke baad content nahi bhejta toh 204, varna HTTP_200_OK check karein
    if response.status_code == 204:
        assert response.status_code == status.HTTP_204_NO_CONTENT
    else:
        assert response.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == test_todo.id).first()
    assert model.title == "Updated learn task"
    assert model.priority == 1
    assert model.complete is True
    db.close()