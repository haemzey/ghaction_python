import os
import tempfile

import pytest

from app import app, init_db


@pytest.fixture()
def client():
    """
    Create a fresh temporary SQLite database for every test.
    """
    db_fd, db_path = tempfile.mkstemp()

    app.config["TESTING"] = True
    app.config["DATABASE"] = db_path

    with app.test_client() as client:
        with app.app_context():
            init_db()

        yield client

    os.close(db_fd)
    os.unlink(db_path)


def create_book(client, **overrides):
    """
    Helper function for creating a test book.
    """
    payload = {
        "title": "The Linux Command Line",
        "author": "William Shotts",
        "isbn": "9781593279523",
        "category": "Linux",
        "published_year": 2019,
        "total_copies": 3,
    }

    payload.update(overrides)

    return client.post("/api/books", json=payload)


def create_member(client, **overrides):
    """
    Helper function for creating a test member.
    """
    payload = {
        "name": "Hamza",
        "email": "hamza@example.com",
        "phone": "03001234567",
    }

    payload.update(overrides)

    return client.post("/api/members", json=payload)


# ============================================================
# Health / Home
# ============================================================


def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "library-management-api",
    }


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200


# ============================================================
# Books
# ============================================================


def test_create_book(client):
    response = create_book(client)

    assert response.status_code == 201

    data = response.get_json()

    assert data["title"] == "The Linux Command Line"
    assert data["author"] == "William Shotts"
    assert data["total_copies"] == 3
    assert data["available_copies"] == 3
    assert data["id"] > 0


def test_create_book_requires_json_object(client):
    response = client.post("/api/books", json=["invalid"])

    assert response.status_code == 400
    assert response.get_json()["error"] == "Request body must be a JSON object."


def test_create_book_requires_title(client):
    response = create_book(client, title="")

    assert response.status_code == 400
    assert "title is required" in response.get_json()["error"]


def test_create_book_requires_author(client):
    response = create_book(client, author="")

    assert response.status_code == 400
    assert "author is required" in response.get_json()["error"]


def test_create_book_rejects_invalid_total_copies(client):
    response = create_book(client, total_copies=0)

    assert response.status_code == 400
    assert "total_copies must be a positive integer" in response.get_json()["error"]


def test_create_book_rejects_negative_year(client):
    response = create_book(client, published_year=-1)

    assert response.status_code == 400
    assert "published_year must be a non-negative integer" in response.get_json()["error"]


def test_create_book_duplicate_isbn(client):
    first = create_book(client)
    assert first.status_code == 201

    second = create_book(client, title="Another Linux Book")

    assert second.status_code == 409
    assert "unique value" in second.get_json()["error"]


def test_get_book(client):
    created = create_book(client)
    book_id = created.get_json()["id"]

    response = client.get(f"/api/books/{book_id}")

    assert response.status_code == 200
    assert response.get_json()["id"] == book_id


def test_get_nonexistent_book(client):
    response = client.get("/api/books/9999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Book not found."


def test_get_book_rejects_invalid_id(client):
    response = client.get("/api/books/abc")

    assert response.status_code == 400
    assert "book_id must be an integer" in response.get_json()["error"]


def test_list_books(client):
    create_book(client, isbn="1111111111")
    create_book(
        client,
        title="Docker Deep Dive",
        author="Nigel Poulton",
        isbn="2222222222",
        category="Docker",
    )

    response = client.get("/api/books")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert len(data["books"]) == 2


def test_search_books(client):
    create_book(client)

    create_book(
        client,
        title="Docker Deep Dive",
        author="Nigel Poulton",
        isbn="2222222222",
        category="Docker",
    )

    response = client.get("/api/books?search=Docker")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert data["books"][0]["title"] == "Docker Deep Dive"


def test_filter_books_by_category(client):
    create_book(client)

    create_book(
        client,
        title="Docker Deep Dive",
        author="Nigel Poulton",
        isbn="2222222222",
        category="Docker",
    )

    response = client.get("/api/books?category=Docker")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert data["books"][0]["category"] == "Docker"


def test_update_book(client):
    created = create_book(client)
    book_id = created.get_json()["id"]

    response = client.put(
        f"/api/books/{book_id}",
        json={
            "title": "Updated Linux Book",
            "author": "Updated Author",
            "total_copies": 5,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["title"] == "Updated Linux Book"
    assert data["author"] == "Updated Author"
    assert data["total_copies"] == 5
    assert data["available_copies"] == 5


def test_update_nonexistent_book(client):
    response = client.put(
        "/api/books/9999",
        json={
            "title": "Unknown",
            "author": "Unknown",
        },
    )

    assert response.status_code == 404


def test_delete_book(client):
    created = create_book(client)
    book_id = created.get_json()["id"]

    response = client.delete(f"/api/books/{book_id}")

    assert response.status_code == 204

    response = client.get(f"/api/books/{book_id}")

    assert response.status_code == 404


# ============================================================
# Members
# ============================================================


def test_create_member(client):
    response = create_member(client)

    assert response.status_code == 201

    data = response.get_json()

    assert data["name"] == "Hamza"
    assert data["email"] == "hamza@example.com"
    assert data["active"] == 1


def test_create_member_normalizes_email(client):
    response = create_member(
        client,
        name="Hamza",
        email="HAMZA@EXAMPLE.COM",
    )

    assert response.status_code == 201
    assert response.get_json()["email"] == "hamza@example.com"


def test_create_member_duplicate_email(client):
    first = create_member(client)
    assert first.status_code == 201

    second = create_member(client)

    assert second.status_code == 409


def test_create_member_requires_name(client):
    response = create_member(client, name="")

    assert response.status_code == 400
    assert "name is required" in response.get_json()["error"]


def test_create_member_requires_valid_email(client):
    response = create_member(client, email="invalid-email")

    assert response.status_code == 400
    assert "email is required and must be valid" in response.get_json()["error"]


def test_list_members(client):
    create_member(client)

    create_member(
        client,
        name="Ali",
        email="ali@example.com",
    )

    response = client.get("/api/members")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 2
    assert len(data["members"]) == 2


def test_update_member(client):
    created = create_member(client)
    member_id = created.get_json()["id"]

    response = client.patch(
        f"/api/members/{member_id}",
        json={
            "name": "Updated Hamza",
            "active": False,
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["name"] == "Updated Hamza"
    assert data["active"] == 0


# ============================================================
# Loans
# ============================================================


def test_borrow_book(client):
    book = create_book(client, total_copies=2)
    book_id = book.get_json()["id"]

    member = create_member(client)
    member_id = member.get_json()["id"]

    response = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member_id,
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["book_id"] == book_id
    assert data["member_id"] == member_id
    assert data["returned_at"] is None
    assert data["book_title"] == "The Linux Command Line"
    assert data["member_name"] == "Hamza"

    book_response = client.get(f"/api/books/{book_id}")

    assert book_response.get_json()["available_copies"] == 1


def test_borrow_book_reduces_available_copies(client):
    book = create_book(client, total_copies=1)
    book_id = book.get_json()["id"]

    member = create_member(client)
    member_id = member.get_json()["id"]

    response = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member_id,
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": 9999,
        },
    )

    assert response.status_code == 404


def test_member_cannot_borrow_same_book_twice(client):
    book = create_book(client, total_copies=2)
    book_id = book.get_json()["id"]

    member = create_member(client)
    member_id = member.get_json()["id"]

    first = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member_id,
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member_id,
        },
    )

    assert second.status_code == 409
    assert "already has an active loan" in second.get_json()["error"]


def test_cannot_borrow_unavailable_book(client):
    book = create_book(client, total_copies=1)
    book_id = book.get_json()["id"]

    member1 = create_member(client)
    member1_id = member1.get_json()["id"]

    member2 = create_member(
        client,
        name="Ali",
        email="ali@example.com",
    )
    member2_id = member2.get_json()["id"]

    first = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member1_id,
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member2_id,
        },
    )

    assert second.status_code == 409
    assert "No available copies" in second.get_json()["error"]


def test_inactive_member_cannot_borrow(client):
    book = create_book(client)

    member = create_member(client, active=False)
    member_id = member.get_json()["id"]

    response = client.post(
        "/api/loans",
        json={
            "book_id": book.get_json()["id"],
            "member_id": member_id,
        },
    )

    assert response.status_code == 409
    assert "Inactive members" in response.get_json()["error"]


def test_return_book(client):
    book = create_book(client, total_copies=1)
    book_id = book.get_json()["id"]

    member = create_member(client)
    member_id = member.get_json()["id"]

    loan = client.post(
        "/api/loans",
        json={
            "book_id": book_id,
            "member_id": member_id,
        },
    )

    loan_id = loan.get_json()["id"]

    book_after_borrow = client.get(f"/api/books/{book_id}")

    assert book_after_borrow.get_json()["available_copies"] == 0

    response = client.post(f"/api/loans/{loan_id}/return")

    assert response.status_code == 200
    assert response.get_json()["returned_at"] is not None

    book_after_return = client.get(f"/api/books/{book_id}")

    assert book_after_return.get_json()["available_copies"] == 1


def test_cannot_return_same_loan_twice(client):
    book = create_book(client)
    member = create_member(client)

    loan = client.post(
        "/api/loans",
        json={
            "book_id": book.get_json()["id"],
            "member_id": member.get_json()["id"],
        },
    )

    loan_id = loan.get_json()["id"]

    first_return = client.post(f"/api/loans/{loan_id}/return")

    assert first_return.status_code == 200

    second_return = client.post(f"/api/loans/{loan_id}/return")

    assert second_return.status_code == 409
    assert "already been returned" in second_return.get_json()["error"]


def test_list_active_loans(client):
    book = create_book(client)
    member = create_member(client)

    loan = client.post(
        "/api/loans",
        json={
            "book_id": book.get_json()["id"],
            "member_id": member.get_json()["id"],
        },
    )

    assert loan.status_code == 201

    response = client.get("/api/loans?active=true")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert data["loans"][0]["returned_at"] is None


def test_list_returned_loans(client):
    book = create_book(client)
    member = create_member(client)

    loan = client.post(
        "/api/loans",
        json={
            "book_id": book.get_json()["id"],
            "member_id": member.get_json()["id"],
        },
    )

    loan_id = loan.get_json()["id"]

    returned = client.post(f"/api/loans/{loan_id}/return")

    assert returned.status_code == 200

    response = client.get("/api/loans?active=false")

    assert response.status_code == 200

    data = response.get_json()

    assert data["count"] == 1
    assert data["loans"][0]["returned_at"] is not None


# ============================================================
# Statistics
# ============================================================


def test_stats(client):
    create_book(client, total_copies=5)

    create_member(client)

    response = client.get("/api/stats")

    assert response.status_code == 200

    data = response.get_json()

    assert data["books"] == 1
    assert data["total_copies"] == 5
    assert data["available_copies"] == 5
    assert data["active_members"] == 1
    assert data["active_loans"] == 0


def test_stats_after_borrow(client):
    book = create_book(client, total_copies=2)
    member = create_member(client)

    response = client.post(
        "/api/loans",
        json={
            "book_id": book.get_json()["id"],
            "member_id": member.get_json()["id"],
        },
    )

    assert response.status_code == 201

    response = client.get("/api/stats")

    assert response.status_code == 200

    data = response.get_json()

    assert data["books"] == 1
    assert data["total_copies"] == 2
    assert data["available_copies"] == 1
    assert data["active_members"] == 1
    assert data["active_loans"] == 1