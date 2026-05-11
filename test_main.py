from repositories import create_book, get_books, get_book, update_book, delete_book
from models import BookIn
from sqlalchemy import inspect


# Test data constants
TEST_BOOKS = [
    {"title": "Carrie", "author": "Stephen King", "isbn": "9780385533454"},
    {"title": "Ready Player One", "author": "Ernest Cline", "isbn": "9780307887443"},
]


class TestMainApp:
    def test_create_app(self, test_app):
        """Test that the FastAPI application is created successfully"""
        assert test_app is not None

    def test_database_initialization(self, test_engine):
        """Test that the books table is created during database initialization"""
        inspector = inspect(test_engine)
        assert "books" in inspector.get_table_names()


# Repository Tests
class TestBookRepository:
    def test_create_book(self, test_db):
        """Test that create_book persists title, author, and isbn and returns an auto-assigned id"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        assert book.title == TEST_BOOKS[0]["title"]
        assert book.author == TEST_BOOKS[0]["author"]
        assert book.isbn == TEST_BOOKS[0]["isbn"]
        assert book.id is not None

    def test_get_books(self, test_db):
        """Test that get_books returns all previously created books"""
        book1 = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        book2 = create_book(test_db, BookIn(**TEST_BOOKS[1]))

        books = get_books(test_db)
        assert len(books) >= 2
        assert any(b.id == book1.id for b in books)
        assert any(b.id == book2.id for b in books)

    def test_get_book(self, test_db):
        """Test that get_book retrieves the correct book by ID"""
        created_book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        retrieved_book = get_book(test_db, created_book.id)
        assert retrieved_book is not None
        assert retrieved_book.id == created_book.id
        assert retrieved_book.title == TEST_BOOKS[0]["title"]
        assert retrieved_book.isbn == TEST_BOOKS[0]["isbn"]

    def test_update_book(self, test_db):
        """Test that update_book modifies title, author, and isbn correctly"""
        book = create_book(test_db, BookIn(**TEST_BOOKS[0]))
        updated_data = BookIn(**TEST_BOOKS[1])
        updated_book = update_book(test_db, book.id, updated_data)
        assert updated_book is not None
        assert updated_book.title == TEST_BOOKS[1]["title"]
        assert updated_book.author == TEST_BOOKS[1]["author"]
        assert updated_book.isbn == TEST_BOOKS[1]["isbn"]

    def test_delete_book(self, test_db):
        """Test that delete_book removes the record and it is no longer retrievable"""
        book = create_book(
            test_db, BookIn(title="To Delete", author="Author", isbn="9780000000001")
        )
        deleted_book = delete_book(test_db, book.id)

        assert deleted_book is not None
        assert deleted_book.id == book.id
        assert get_book(test_db, book.id) is None

    def test_get_nonexistent_book(self, test_db):
        """Test that get_book returns None for a nonexistent ID"""
        assert get_book(test_db, 999999) is None

    def test_update_nonexistent_book(self, test_db):
        """Test that update_book returns None for a nonexistent ID"""
        assert update_book(test_db, 999999, BookIn(**TEST_BOOKS[0])) is None

    def test_delete_nonexistent_book(self, test_db):
        """Test that delete_book returns None for a nonexistent ID"""
        assert delete_book(test_db, 999999) is None

    def test_get_books_pagination(self, test_db):
        """Test that skip and limit pagination parameters work correctly"""
        create_book(test_db, BookIn(**TEST_BOOKS[0]))
        create_book(test_db, BookIn(**TEST_BOOKS[1]))

        books_page1 = get_books(test_db, skip=0, limit=1)
        assert len(books_page1) == 1

        books_page2 = get_books(test_db, skip=1, limit=1)
        assert len(books_page2) == 1

        assert books_page1[0].id != books_page2[0].id

        books_empty = get_books(test_db, skip=0, limit=0)
        assert len(books_empty) == 0


# HTTP / Router Tests
class TestBooksRouter:
    def test_create_book_http(self, client):
        """Test POST /api/books/ creates a book and returns 201"""
        payload = {"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["author"] == payload["author"]
        assert data["isbn"] == payload["isbn"]
        assert "id" in data

    def test_create_book_missing_field_returns_422(self, client):
        """Test POST /api/books/ with missing required field returns 422"""
        payload = {"title": "No Author or ISBN"}
        response = client.post("/api/books/", json=payload)
        assert response.status_code == 422

    def test_get_books_http(self, client):
        """Test GET /api/books/ returns a list of books"""
        client.post(
            "/api/books/",
            json={"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"},
        )
        response = client.get("/api/books/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_book_http(self, client):
        """Test GET /api/books/{id} returns the correct book"""
        created = client.post(
            "/api/books/",
            json={"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"},
        ).json()
        response = client.get(f"/api/books/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_book_not_found(self, client):
        """Test GET /api/books/{id} returns 404 for nonexistent ID"""
        response = client.get("/api/books/999999")
        assert response.status_code == 404

    def test_update_book_http(self, client):
        """Test PUT /api/books/{id} updates all fields correctly"""
        created = client.post(
            "/api/books/",
            json={"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"},
        ).json()
        update_payload = {
            "title": "Dune Messiah",
            "author": "Frank Herbert",
            "isbn": "9780593098233",
        }
        response = client.put(f"/api/books/{created['id']}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_payload["title"]
        assert data["isbn"] == update_payload["isbn"]

    def test_update_book_not_found(self, client):
        """Test PUT /api/books/{id} returns 404 for nonexistent ID"""
        response = client.put(
            "/api/books/999999",
            json={"title": "X", "author": "Y", "isbn": "9780000000000"},
        )
        assert response.status_code == 404

    def test_delete_book_http(self, client):
        """Test DELETE /api/books/{id} removes the book and returns 200"""
        created = client.post(
            "/api/books/",
            json={"title": "Dune", "author": "Frank Herbert", "isbn": "9780441013593"},
        ).json()
        response = client.delete(f"/api/books/{created['id']}")
        assert response.status_code == 200

        follow_up = client.get(f"/api/books/{created['id']}")
        assert follow_up.status_code == 404

    def test_delete_book_not_found(self, client):
        """Test DELETE /api/books/{id} returns 404 for nonexistent ID"""
        response = client.delete("/api/books/999999")
        assert response.status_code == 404
