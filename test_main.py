from sqlalchemy import inspect

from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn


# Test data constants
TEST_BOOKS = [
    {
        "title": "Carrie",
        "author": "Stephen King",
        "isbn": "978-0-385-08695-0",
        "publisher": "Doubleday",
    },
    {
        "title": "Ready Player One",
        "author": "Ernest Cline",
        "isbn": "978-0-307-88743-6",
        "publisher": "Crown Publishers",
    },
]


class TestMainApp:
    def test_create_app(self, test_app):
        """Test application creation."""
        assert test_app is not None

    def test_database_initialization(self, test_engine):
        """Test database initialization."""
        inspector = inspect(test_engine)
        assert "books" in inspector.get_table_names()


# Repository Tests
class TestBookRepository:
    def test_create_book(self, test_db):
        """Test creating a new book."""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        assert book.title == TEST_BOOKS[0]["title"]
        assert book.author == TEST_BOOKS[0]["author"]
        assert book.isbn == TEST_BOOKS[0]["isbn"]
        assert book.publisher == TEST_BOOKS[0]["publisher"]
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test getting all books."""
        book1 = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        book2 = create_book(test_db, BookIn(**TEST_BOOKS[1]))

        books = get_books(test_db)
        assert len(books) == 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_book(self, test_db):
        """Test getting a specific book."""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]
        assert retrieved_book.publisher == TEST_BOOKS[0]["publisher"]

    def test_update_book(self, test_db):
        """Test updating a book."""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        updated_data = BookIn(**TEST_BOOKS[1])
        updated_book = update_book(test_db, book.id, updated_data)
        assert updated_book is not None
        assert updated_book.title == TEST_BOOKS[1]["title"]
        assert updated_book.author == TEST_BOOKS[1]["author"]
        assert updated_book.isbn == TEST_BOOKS[1]["isbn"]
        assert updated_book.publisher == TEST_BOOKS[1]["publisher"]

    def test_delete_book(self, test_db):
        """Test deleting a book."""
        book = create_book(
            test_db,
            BookIn(
                title="To Delete",
                author="Author",
                isbn="000-0-000-00000-0",
                publisher="Test Publisher",
            ),
        )
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_nonexistent_operations(self, test_db):
        """Test operations on nonexistent books."""
        dummy = BookIn(
            title="Test",
            author="Test",
            isbn="000-0-000-00000-1",
            publisher="Test Publisher",
        )
        assert get_book(test_db, 999999) is None
        assert update_book(test_db, 999999, dummy) is None
        assert delete_book(test_db, 999999) is None


# HTTP / Router Tests
class TestBookRoutes:
    def test_create_book_201(self, client):
        """POST /api/books/ returns 201 and includes all fields in response."""
        payload = TEST_BOOKS[0]
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert data["publisher"] == payload["publisher"]
        assert "id" in data

    def test_create_book_missing_field_422(self, client):
        """POST /api/books/ with missing required field returns 422."""
        response = client.post("/api/books/", json={"title": "No Author"})
        assert response.status_code == 422

    def test_get_books_200(self, client):
        """GET /api/books/ returns 200 and a list."""
        client.post("/api/books/", json=TEST_BOOKS[0])
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_books_pagination(self, client):
        """GET /api/books/ respects skip and limit parameters."""
        client.post("/api/books/", json=TEST_BOOKS[0])
        client.post("/api/books/", json=TEST_BOOKS[1])
        response = client.get("/api/books/?skip=0&limit=1")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_book_200(self, client):
        """GET /api/books/{id} returns 200 for an existing book."""
        created = client.post("/api/books/", json=TEST_BOOKS[0]).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]
        assert response.json()["publisher"] == TEST_BOOKS[0]["publisher"]

    def test_get_book_404(self, client):
        """GET /api/books/{id} returns 404 for a non-existent book."""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_200(self, client):
        """PUT /api/books/{id} returns 200 and updated data."""
        created = client.post("/api/books/", json=TEST_BOOKS[0]).json()
        response = client.put(f"/api/books/{created['id']}", json=TEST_BOOKS[1])
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == TEST_BOOKS[1]["title"]
        assert data["publisher"] == TEST_BOOKS[1]["publisher"]

    def test_update_book_404(self, client):
        """PUT /api/books/{id} returns 404 for a non-existent book."""
        response = client.put("/api/books/999999", json=TEST_BOOKS[0])
        assert response.status_code == 404

    def test_delete_book_200(self, client):
        """DELETE /api/books/{id} returns 200 and the deleted book."""
        created = client.post("/api/books/", json=TEST_BOOKS[0]).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_delete_book_404(self, client):
        """DELETE /api/books/{id} returns 404 for a non-existent book."""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
