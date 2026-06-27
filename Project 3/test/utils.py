import pytest
from sqlalchemy import create_engine, text  # 👈 'text' ko yahan add kiya
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from TodoApp.models import Todos
from sqlalchemy.pool import StaticPool

# 1. App aur Database se standard imports
from TodoApp.main import app 
from TodoApp.database import Base

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

