from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn
from sqlalchemy import inspect


# Test data constants — each test that inserts uses its own unique ISBNs
# to work safely within the shared SQLite test session.
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385533225"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887443"},
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
        book = create_book(test_db, BookIn(title="Carrie", author="Stephen King", isbn="9780006280002"))
        assert book.title == "Carrie"
        assert book.author == "Stephen King"
        assert book.isbn == "9780006280002"
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test getting all books"""
        book1 = create_book(test_db, BookIn(title="Carrie", author="Stephen King", isbn="9780006280019"))
        book2 = create_book(test_db, BookIn(title="Ready Player One", author="Ernest Cline", isbn="9780006280026"))

        books = get_books(test_db)
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_book(self, test_db):
        """Test getting a specific book"""
        created_book = create_book(test_db, BookIn(title="Carrie", author="Stephen King", isbn="9780006280033"))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == "Carrie"
        assert retrieved_book.isbn == "9780006280033"

    def test_update_book(self, test_db):
        """Test updating a book"""
        book = create_book(test_db, BookIn(title="Carrie", author="Stephen King", isbn="9780006280040"))
        updated_book = update_book(test_db, book.id, BookIn(title="Ready Player One", author="Ernest Cline", isbn="9780006280057"))
        assert updated_book is not None
        assert updated_book.title == "Ready Player One"
        assert updated_book.author == "Ernest Cline"
        assert updated_book.isbn == "9780006280057"

    def test_delete_book(self, test_db):
        """Test deleting a book"""
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="0306406152"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="9780385533225")) is None
        assert delete_book(test_db, 999999) is None


# HTTP-layer (router) tests
class TestBooksAPI:
    def test_create_book(self, client):
        """Test POST /api/books/ returns 201 with isbn in response"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_invalid_isbn(self, client):
        """Test POST /api/books/ with invalid ISBN returns 422"""
        payload = {"title": "Bad Book", "author": "Nobody", "isbn": "not-an-isbn"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_get_books(self, client):
        """Test GET /api/books/ returns 200"""
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_books_pagination_bounds(self, client):
        """Test GET /api/books/ rejects out-of-bounds limit"""
        response = client.get("/api/books/?limit=0")
        assert response.status_code == 422
        response = client.get("/api/books/?limit=101")
        assert response.status_code == 422

    def test_get_book_not_found(self, client):
        """Test GET /api/books/{id} returns 404 for missing book"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_get_book_found(self, client):
        """Test GET /api/books/{id} returns 200 for existing book"""
        created = client.post(
            "/api/books/",
            json={"title": "Foundation", "author": "Isaac Asimov", "isbn": "9780553293357"},
        )
        assert created.status_code == 201
        book_id = created.json()["id"]
        response = client.get(f"/api/books/{book_id}")
        assert response.status_code == 200
        assert response.json()["isbn"] == "9780553293357"

    def test_update_book(self, client):
        """Test PUT /api/books/{id} returns 200"""
        created = client.post(
            "/api/books/",
            json={"title": "Old Title", "author": "Old Author", "isbn": "9780743273565"},
        )
        assert created.status_code == 201
        book_id = created.json()["id"]
        update_payload = {"title": "New Title", "author": "New Author", "isbn": "9780062316097"}
        response = client.put(f"/api/books/{book_id}", json=update_payload)
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"
        assert response.json()["isbn"] == "9780062316097"

    def test_update_book_not_found(self, client):
        """Test PUT /api/books/{id} returns 404 for missing book"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780385533225"},
        )
        assert response.status_code == 404

    def test_delete_book(self, client):
        """Test DELETE /api/books/{id} returns 200"""
        created = client.post(
            "/api/books/",
            json={"title": "To Delete", "author": "Author", "isbn": "9780525559474"},
        )
        assert created.status_code == 201
        book_id = created.json()["id"]
        response = client.delete(f"/api/books/{book_id}")
        assert response.status_code == 200
        # Confirm deletion
        assert client.get(f"/api/books/{book_id}").status_code == 404

    def test_delete_book_not_found(self, client):
        """Test DELETE /api/books/{id} returns 404 for missing book"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
