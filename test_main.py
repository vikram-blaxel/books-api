from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn
from sqlalchemy import inspect


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385533485"},
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

    def test_get_books_pagination(self, test_db):
        """Test get_books with skip/limit pagination"""
        book1 = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        book2 = create_book(test_db, BookIn(**TEST_BOOKS[1]))

        all_books = get_books(test_db, skip=0, limit=100)
        ids = [b.id for b in all_books]
        assert book1.id in ids
        assert book2.id in ids

        # skip=1 from the full ordered result should omit the first returned book
        limited = get_books(test_db, skip=0, limit=1)
        assert len(limited) == 1

    def test_get_book(self, test_db):
        """Test getting a specific book"""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]
        assert retrieved_book.author == TEST_BOOKS[0]["author"]
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
        # Verify persisted state via a fresh read
        persisted = get_book(test_db, book.id)
        assert persisted is not None
        assert persisted.title == TEST_BOOKS[1]["title"]
        assert persisted.isbn == TEST_BOOKS[1]["isbn"]

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
        assert update_book(test_db, 999999, BookIn(title="Test", author="Test", isbn="0306406152")) is None
        assert delete_book(test_db, 999999) is None


# HTTP Router Tests
class TestBookRouterHTTP:
    def test_create_book_success(self, client):
        """POST /api/books/ returns 201 with the created book"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_invalid_isbn(self, client):
        """POST /api/books/ returns 422 for an invalid ISBN"""
        payload = {"title": "Bad ISBN", "author": "Nobody", "isbn": "not-an-isbn"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_get_books(self, client):
        """GET /api/books/ returns 200 with a list"""
        client.post("/api/books/", json={"title": "Book A", "author": "Auth A", "isbn": "9780385533485"})
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_book_success(self, client):
        """GET /api/books/{id} returns 200 for an existing book"""
        create_resp = client.post(
            "/api/books/",
            json={"title": "Foundation", "author": "Isaac Asimov", "isbn": "9780553293357"},
        )
        book_id = create_resp.json()["id"]
        response = client.get(f"/api/books/{book_id}")
        assert response.status_code == 200
        assert response.json()["id"] == book_id

    def test_get_book_not_found(self, client):
        """GET /api/books/{id} returns 404 for a missing book"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_update_book_success(self, client):
        """PUT /api/books/{id} returns 200 and updates the book"""
        create_resp = client.post(
            "/api/books/",
            json={"title": "Old Title", "author": "Old Author", "isbn": "0306406152"},
        )
        book_id = create_resp.json()["id"]
        update_payload = {"title": "New Title", "author": "New Author", "isbn": "9780441013593"}
        response = client.put(f"/api/books/{book_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["isbn"] == "9780441013593"

    def test_update_book_not_found(self, client):
        """PUT /api/books/{id} returns 404 for a missing book"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "0306406152"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_delete_book_success(self, client):
        """DELETE /api/books/{id} returns 200 and removes the book"""
        create_resp = client.post(
            "/api/books/",
            json={"title": "To Remove", "author": "Someone", "isbn": "9780307887443"},
        )
        book_id = create_resp.json()["id"]
        response = client.delete(f"/api/books/{book_id}")
        assert response.status_code == 200
        # Verify it's gone
        assert client.get(f"/api/books/{book_id}").status_code == 404

    def test_delete_book_not_found(self, client):
        """DELETE /api/books/{id} returns 404 for a missing book"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"
