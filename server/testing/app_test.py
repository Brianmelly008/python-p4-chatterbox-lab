import pytest
from datetime import datetime
from app import app, db
from models import Message

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def create_message():
    message = Message(body="Hello 👋", username="Liza")
    db.session.add(message)
    db.session.commit()
    yield message
    db.session.delete(message)
    db.session.commit()

def test_has_correct_columns(client):
    with app.app_context():
        message = Message(
            body="Hello 👋",
            username="Liza"
        )
        db.session.add(message)
        db.session.commit()

        assert message.body == "Hello 👋"
        assert message.username == "Liza"
        assert isinstance(message.created_at, datetime)

        db.session.delete(message)
        db.session.commit()

def test_returns_list_of_json_objects_for_all_messages_in_database(client):
    with app.app_context():
        message = Message(body="Test message", username="Tester")
        db.session.add(message)
        db.session.commit()

        response = client.get('/messages')
        records = Message.query.all()

        for message in response.json:
            assert message['id'] in [record.id for record in records]
            assert message['body'] in [record.body for record in records]

        db.session.delete(message)
        db.session.commit()

def test_creates_new_message_in_the_database(client):
    with app.app_context():
        response = client.post(
            '/messages',
            json={"body": "Hello 👋", "username": "Liza"}
        )
        assert response.status_code == 201

        h = Message.query.filter_by(body="Hello 👋", username="Liza").first()
        assert h is not None

        db.session.delete(h)
        db.session.commit()

def test_returns_data_for_newly_created_message_as_json(client):
    with app.app_context():
        response = client.post(
            '/messages',
            json={"body": "Hello 👋", "username": "Liza"}
        )
        assert response.content_type == 'application/json'
        assert response.json["body"] == "Hello 👋"
        assert response.json["username"] == "Liza"

        h = Message.query.filter_by(body="Hello 👋", username="Liza").first()
        assert h is not None

        db.session.delete(h)
        db.session.commit()

def test_updates_body_of_message_in_database(client, create_message):
    with app.app_context():
        id = create_message.id
        response = client.patch(
            f'/messages/{id}',
            json={"body": "Goodbye 👋"}
        )
        assert response.status_code == 200

        updated_message = Message.query.get(id)
        assert updated_message.body == "Goodbye 👋"

def test_returns_data_for_updated_message_as_json(client, create_message):
    with app.app_context():
        id = create_message.id
        response = client.patch(
            f'/messages/{id}',
            json={"body": "Goodbye 👋"}
        )
        assert response.content_type == 'application/json'
        assert response.json["body"] == "Goodbye 👋"

def test_deletes_message_from_database(client, create_message):
    with app.app_context():
        response = client.delete(f'/messages/{create_message.id}')
        assert response.status_code == 200

        h = Message.query.filter_by(id=create_message.id).first()
        assert h is None
