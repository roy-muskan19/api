import pytest



def test_equal_or_not_equal():
    assert 3==3
    assert 3!=2

def test_type():
    assert type ("hello" is str)



class Student:
    def __init__(self, first_name: str, last_name: str, major: str, years: int):
        self.first_name = first_name
        self.last_name = last_name
        self.major = major
        self.years = years


@pytest.fixture
def default_employee():
    return Student(first_name="Gauresh", last_name="Dev", major="Computer Science", years=3)

def test_person_initialization(default_employee):
    
    assert default_employee.first_name=="Gauresh" , 'firstname should be Gauresh'
    assert default_employee.last_name=="Dev" ,'lastname should be Dev'
    assert default_employee.major=="Computer Science"
    assert default_employee.years==3
    