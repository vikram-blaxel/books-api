from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn
from sqlalchemy import inspect


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385533225"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887436"},
]


class TestMainApp:
    def test_create_app(self, test_app):
        """Test application creation"""
        assert test_app is not None

    def test_database_initialization(self, test_engine):
        """Test database initialization"""
        inspector = inspect(test_engine)
        assert "books" in inspector.get_table_names()


# Repository Tests
class TestBookRepository:
    def test_create_book(self, test_db):
        """Test creating a new book"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        assert book.title == TEST_BOOKS[0]["title"]
        assert book.author == TEST_BOOKS[0]["author"]
        assert book.isbn == TEST_BOOKS[0]["isbn"]
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test getting all books"""
        book1 = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        book2 = create_book(test_db, BookIn(**TEST_BOOKS[1]))

        books = get_books(test_db)
        assert len(books) >= 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_book(self, test_db):
        """Test getting a specific book"""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]

    def test_update_book(self, test_db):
        """Test updating a book"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        updated_data = BookIn(**TEST_BOOKS[1])
        updated_book = update_book(test_db, book.id, updated_data)
        assert updated_book is not None
        assert updated_book.title == TEST_BOOKS[1]["title"]
        assert updated_book.author == TEST_BOOKS[1]["author"]
        assert updated_book.isbn == TEST_BOOKS[1]["isbn"]

    def test_delete_book(self, test_db):
        """Test deleting a book"""
        book = create_book(
            test_db, BookIn(title="To Delete", author="Author", isbn="9780000000002")
        )
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert (
            update_book(
                test_db, 999999, BookIn(title="Test", author="Test", isbn="9780000000019")
            )
            is None
        )
        assert delete_book(test_db, 999999) is None


# HTTP-layer (integration) Tests
class TestBookAPI:
    def test_create_book(self, client):
        """Test POST /api/books/ returns 201 with created book"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_get_books(self, client):
        """Test GET /api/books/ returns a list"""
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_book_not_found(self, client):
        """Test GET /api/books/{id} returns 404 for missing book"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book(self, client):
        """Test PUT /api/books/{id} updates the book"""
        create_payload = {
            "title": "1984",
            "author": "George Orwell",
            "isbn": "9780451524935",
        }
        created = client.post("/api/books/", json=create_payload)
        assert created.status_code == 201
        book_id = created.json()["id"]

        update_payload = {
            "title": "Animal Farm",
            "author": "George Orwell",
            "isbn": "9780451526342",
        }
        response = client.put(f"/api/books/{book_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_payload["title"]
        assert data["isbn"] == update_payload["isbn"]

    def test_update_book_not_found(self, client):
        """Test PUT /api/books/{id} returns 404 for missing book"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780000000033"},
        )
        assert response.status_code == 404

    def test_delete_book(self, client):
        """Test DELETE /api/books/{id} deletes the book"""
        create_payload = {
            "title": "Brave New World",
            "author": "Aldous Huxley",
            "isbn": "9780060850524",
        }
        created = client.post("/api/books/", json=create_payload)
        assert created.status_code == 201
        book_id = created.json()["id"]

        response = client.delete(f"/api/books/{book_id}")
        assert response.status_code == 200

        # Confirm deleted
        get_response = client.get(f"/api/books/{book_id}")
        assert get_response.status_code == 404

    def test_delete_book_not_found(self, client):
        """Test DELETE /api/books/{id} returns 404 for missing book"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
