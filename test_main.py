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
        book = create_book(
            test_db, BookIn(title="To Delete", author="Author", isbn="9780000000001")
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
                test_db,
                999999,
                BookIn(title="Test", author="Test", isbn="9780000000002"),
            )
            is None
        )
        assert delete_book(test_db, 999999) is None


# Router / HTTP Integration Tests
class TestBookRouter:
    def test_create_book_http(self, client):
        """POST /api/books/ creates a book and returns 201"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_invalid_payload(self, client):
        """POST /api/books/ with missing fields returns 422"""
        response = client.post("/api/books/", json={"title": "No Author or ISBN"})
        assert response.status_code == 422

    def test_get_books_http(self, client):
        """GET /api/books/ returns a list"""
        client.post(
            "/api/books/",
            json={"title": "Book A", "author": "Author A", "isbn": "9780000000010"},
        )
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_books_pagination(self, client):
        """GET /api/books/ respects skip and limit parameters"""
        for i in range(3):
            client.post(
                "/api/books/",
                json={
                    "title": f"Paginated Book {i}",
                    "author": "Author",
                    "isbn": f"978000000002{i}",
                },
            )
        response = client.get("/api/books/?skip=0&limit=2")
        assert response.status_code == 200
        assert len(response.json()) <= 2

    def test_get_book_http(self, client):
        """GET /api/books/{id} returns a single book"""
        create_resp = client.post(
            "/api/books/",
            json={"title": "Neuromancer", "author": "William Gibson", "isbn": "9780441569595"},
        )
        book_id = create_resp.json()["id"]
        response = client.get(f"/api/books/{book_id}")
        assert response.status_code == 200
        assert response.json()["id"] == book_id

    def test_get_book_not_found(self, client):
        """GET /api/books/{id} returns 404 for unknown ID"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_http(self, client):
        """PUT /api/books/{id} updates a book"""
        create_resp = client.post(
            "/api/books/",
            json={"title": "Old Title", "author": "Old Author", "isbn": "9780000000030"},
        )
        book_id = create_resp.json()["id"]
        update_payload = {
            "title": "New Title",
            "author": "New Author",
            "isbn": "9780000000031",
        }
        response = client.put(f"/api/books/{book_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["isbn"] == "9780000000031"

    def test_update_book_not_found(self, client):
        """PUT /api/books/{id} returns 404 for unknown ID"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780000000032"},
        )
        assert response.status_code == 404

    def test_delete_book_http(self, client):
        """DELETE /api/books/{id} deletes a book"""
        create_resp = client.post(
            "/api/books/",
            json={"title": "To Remove", "author": "Someone", "isbn": "9780000000040"},
        )
        book_id = create_resp.json()["id"]
        response = client.delete(f"/api/books/{book_id}")
        assert response.status_code == 200
        assert response.json()["id"] == book_id
        # Confirm it's gone
        assert client.get(f"/api/books/{book_id}").status_code == 404

    def test_delete_book_not_found(self, client):
        """DELETE /api/books/{id} returns 404 for unknown ID"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
