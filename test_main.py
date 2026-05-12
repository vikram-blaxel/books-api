from sqlalchemy import inspect

from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


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
        assert retrieved_book.isbn == TEST_BOOKS[0]["isbn"]

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
        book = create_book(test_db, BookIn(title="To Delete", author="Author", isbn="9780000000001"))
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books"""
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="9780000000002")) is None
        assert delete_book(test_db, 999999) is None


# HTTP Layer Tests
class TestHTTPEndpoints:
    def test_create_book_http(self, client):
        """Test POST /api/books/ returns 201 with correct fields"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_get_books_http(self, client):
        """Test GET /api/books/ returns 200 and a list"""
        # Create a book first so the list is non-empty
        client.post(
            "/api/books/",
            json={"title": "Foundation", "author": "Isaac Asimov", "isbn": "9780553293357"},
        )
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_book_http(self, client):
        """Test GET /api/books/{id} returns 200 for existing book"""
        created = client.post(
            "/api/books/",
            json={"title": "Neuromancer", "author": "William Gibson", "isbn": "9780441569595"},
        ).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["isbn"] == "9780441569595"

    def test_get_book_not_found_http(self, client):
        """Test GET /api/books/{id} returns 404 for missing book"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_http(self, client):
        """Test PUT /api/books/{id} updates all fields including isbn"""
        created = client.post(
            "/api/books/",
            json={"title": "Old Title", "author": "Old Author", "isbn": "9780000000003"},
        ).json()
        update_payload = {"title": "New Title", "author": "New Author", "isbn": "9780000000004"}
        response = client.put(f"/api/books/{created['id']}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["author"] == "New Author"
        assert data["isbn"] == "9780000000004"

    def test_update_book_not_found_http(self, client):
        """Test PUT /api/books/{id} returns 404 for missing book"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780000000005"},
        )
        assert response.status_code == 404

    def test_delete_book_http(self, client):
        """Test DELETE /api/books/{id} removes the book"""
        created = client.post(
            "/api/books/",
            json={"title": "To Remove", "author": "Someone", "isbn": "9780000000006"},
        ).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200
        # Confirm it's gone
        assert client.get(f"/api/books/{created['id']}").status_code == 404

    def test_delete_book_not_found_http(self, client):
        """Test DELETE /api/books/{id} returns 404 for missing book"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404

    def test_create_book_invalid_isbn_http(self, client):
        """Test POST /api/books/ returns 422 for invalid ISBN"""
        response = client.post(
            "/api/books/",
            json={"title": "Bad Book", "author": "Author", "isbn": "not-an-isbn"},
        )
        assert response.status_code == 422

    def test_create_book_missing_fields_http(self, client):
        """Test POST /api/books/ returns 422 when required fields are absent"""
        response = client.post("/api/books/", json={"title": "Incomplete"})
        assert response.status_code == 422

    def test_get_books_pagination_http(self, client):
        """Test GET /api/books/ pagination parameters"""
        # Create two books to paginate
        client.post(
            "/api/books/",
            json={"title": "Page Book 1", "author": "Author A", "isbn": "9780000000007"},
        )
        client.post(
            "/api/books/",
            json={"title": "Page Book 2", "author": "Author B", "isbn": "9780000000008"},
        )
        # limit=1 should return exactly one book
        response = client.get("/api/books/?limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1
        # skip beyond total should return empty list
        response = client.get("/api/books/?skip=10000&limit=10")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_book_duplicate_isbn_http(self, client):
        """Test POST /api/books/ returns 409 for duplicate ISBN"""
        payload = {"title": "Unique Book", "author": "Author", "isbn": "9780000000009"}
        client.post("/api/books/", json=payload)
        response = client.post(
            "/api/books/",
            json={"title": "Other Title", "author": "Other Author", "isbn": "9780000000009"},
        )
        assert response.status_code == 409
