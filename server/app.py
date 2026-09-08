import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, g, jsonify, render_template, request


app = Flask(
    __name__,
    template_folder="../client/templates",
    static_folder="../client/static",
    static_url_path="/static",
)
app.config["DATABASE"] = os.environ.get(
    "LIBRARY_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db"),
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    isbn TEXT UNIQUE,
    category TEXT,
    published_year INTEGER,
    total_copies INTEGER NOT NULL DEFAULT 1 CHECK (total_copies > 0),
    available_copies INTEGER NOT NULL DEFAULT 1 CHECK (
        available_copies >= 0 AND available_copies <= total_copies
    ),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    borrowed_at TEXT NOT NULL,
    due_date TEXT NOT NULL,
    returned_at TEXT,
    CHECK (returned_at IS NULL OR returned_at >= borrowed_at)
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_loans_active ON loans(returned_at);
"""


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        get_db().executescript(SCHEMA)
        get_db().commit()


def row_to_dict(row):
    return dict(row) if row else None


def error(message, status=400):
    return jsonify({"error": message}), status


def json_body(required=True):
    body = request.get_json(silent=True)
    if required and not isinstance(body, dict):
        return None, error("Request body must be a JSON object.", 400)
    return body or {}, None


def positive_int(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return value


def parse_id(value, field_name="id"):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer.") from None
    return positive_int(parsed, field_name)


def handle_errors(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except ValueError as exc:
            return error(str(exc))
        except sqlite3.IntegrityError as exc:
            message = str(exc).lower()
            if "unique" in message:
                return error("A record with that unique value already exists.", 409)
            return error("The request violates a data constraint.", 409)

    return wrapped


def validate_book_payload(payload, existing=None):
    title = payload.get("title", existing["title"] if existing else None)
    author = payload.get("author", existing["author"] if existing else None)
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title is required and must be a non-empty string.")
    if not isinstance(author, str) or not author.strip():
        raise ValueError("author is required and must be a non-empty string.")

    isbn = payload.get("isbn", existing["isbn"] if existing else None)
    category = payload.get("category", existing["category"] if existing else None)
    year = payload.get("published_year", existing["published_year"] if existing else None)
    total = payload.get("total_copies", existing["total_copies"] if existing else 1)

    if isbn is not None and (not isinstance(isbn, str) or not isbn.strip()):
        raise ValueError("isbn must be a non-empty string when provided.")
    if category is not None and not isinstance(category, str):
        raise ValueError("category must be a string when provided.")
    if year is not None and (
        isinstance(year, bool) or not isinstance(year, int) or year < 0
    ):
        raise ValueError("published_year must be a non-negative integer.")
    positive_int(total, "total_copies")

    available = existing["available_copies"] if existing else total
    if total < (existing["total_copies"] - existing["available_copies"] if existing else 0):
        raise ValueError("total_copies cannot be lower than the number of active loans.")
    return (
        title.strip(),
        author.strip(),
        isbn.strip() if isinstance(isbn, str) else None,
        category.strip() if isinstance(category, str) else None,
        year,
        total,
        available,
    )


def get_book(book_id):
    return get_db().execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def get_member(member_id):
    return get_db().execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "library-management-api"})


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/books")
def list_books():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    query = "SELECT * FROM books WHERE 1 = 1"
    params = []
    if search:
        query += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ?)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY title COLLATE NOCASE"
    rows = get_db().execute(query, params).fetchall()
    return jsonify({"books": [row_to_dict(row) for row in rows], "count": len(rows)})


@app.post("/api/books")
@handle_errors
def create_book():
    payload, body_error = json_body()
    if body_error:
        return body_error
    title, author, isbn, category, year, total, available = validate_book_payload(payload)
    now = utc_now()
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO books
            (title, author, isbn, category, published_year, total_copies,
             available_copies, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (title, author, isbn, category, year, total, available, now, now),
    )
    db.commit()
    return jsonify(row_to_dict(get_book(cursor.lastrowid))), 201


@app.get("/api/books/<book_id>")
@handle_errors
def read_book(book_id):
    book = get_book(parse_id(book_id, "book_id"))
    if not book:
        return error("Book not found.", 404)
    return jsonify(row_to_dict(book))


@app.put("/api/books/<book_id>")
@handle_errors
def update_book(book_id):
    book_id = parse_id(book_id, "book_id")
    existing = get_book(book_id)
    if not existing:
        return error("Book not found.", 404)
    payload, body_error = json_body()
    if body_error:
        return body_error
    title, author, isbn, category, year, total, available = validate_book_payload(
        payload, existing
    )
    db = get_db()
    db.execute(
        """
        UPDATE books
        SET title = ?, author = ?, isbn = ?, category = ?, published_year = ?,
            total_copies = ?, available_copies = ?, updated_at = ?
        WHERE id = ?
        """,
        (title, author, isbn, category, year, total, available, utc_now(), book_id),
    )
    db.commit()
    return jsonify(row_to_dict(get_book(book_id)))


@app.delete("/api/books/<book_id>")
@handle_errors
def delete_book(book_id):
    book_id = parse_id(book_id, "book_id")
    if not get_book(book_id):
        return error("Book not found.", 404)
    active_loan = get_db().execute(
        "SELECT 1 FROM loans WHERE book_id = ? AND returned_at IS NULL", (book_id,)
    ).fetchone()
    if active_loan:
        return error("A book with active loans cannot be deleted.", 409)
    db = get_db()
    db.execute("DELETE FROM loans WHERE book_id = ?", (book_id,))
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    return "", 204


@app.get("/api/members")
def list_members():
    rows = get_db().execute(
        "SELECT * FROM members ORDER BY name COLLATE NOCASE"
    ).fetchall()
    return jsonify({"members": [row_to_dict(row) for row in rows], "count": len(rows)})


@app.post("/api/members")
@handle_errors
def create_member():
    payload, body_error = json_body()
    if body_error:
        return body_error
    name = payload.get("name")
    email = payload.get("email")
    phone = payload.get("phone")
    if not isinstance(name, str) or not name.strip():
        return error("name is required and must be a non-empty string.")
    if not isinstance(email, str) or "@" not in email:
        return error("email is required and must be valid.")
    if phone is not None and not isinstance(phone, str):
        return error("phone must be a string when provided.")
    db = get_db()
    cursor = db.execute(
        "INSERT INTO members (name, email, phone, created_at) VALUES (?, ?, ?, ?)",
        (name.strip(), email.strip().lower(), phone.strip() if phone else None, utc_now()),
    )
    db.commit()
    return jsonify(row_to_dict(get_member(cursor.lastrowid))), 201


@app.patch("/api/members/<member_id>")
@handle_errors
def update_member(member_id):
    member_id = parse_id(member_id, "member_id")
    existing = get_member(member_id)
    if not existing:
        return error("Member not found.", 404)
    payload, body_error = json_body()
    if body_error:
        return body_error
    name = payload.get("name", existing["name"])
    email = payload.get("email", existing["email"])
    phone = payload.get("phone", existing["phone"])
    active = payload.get("active", existing["active"])
    if not isinstance(name, str) or not name.strip():
        return error("name must be a non-empty string.")
    if not isinstance(email, str) or "@" not in email:
        return error("email must be valid.")
    if active not in (0, 1, False, True):
        return error("active must be a boolean.")
    db = get_db()
    db.execute(
        "UPDATE members SET name = ?, email = ?, phone = ?, active = ? WHERE id = ?",
        (name.strip(), email.strip().lower(), phone, int(bool(active)), member_id),
    )
    db.commit()
    return jsonify(row_to_dict(get_member(member_id)))


@app.post("/api/loans")
@handle_errors
def borrow_book():
    payload, body_error = json_body()
    if body_error:
        return body_error
    book_id = parse_id(payload.get("book_id"), "book_id")
    member_id = parse_id(payload.get("member_id"), "member_id")
    loan_days = payload.get("loan_days", 14)
    positive_int(loan_days, "loan_days")
    book = get_book(book_id)
    member = get_member(member_id)
    if not book:
        return error("Book not found.", 404)
    if not member:
        return error("Member not found.", 404)
    if not member["active"]:
        return error("Inactive members cannot borrow books.", 409)
    if book["available_copies"] < 1:
        return error("No available copies of this book.", 409)
    db = get_db()
    already_borrowed = db.execute(
        "SELECT 1 FROM loans WHERE book_id = ? AND member_id = ? AND returned_at IS NULL",
        (book_id, member_id),
    ).fetchone()
    if already_borrowed:
        return error("This member already has an active loan for this book.", 409)
    borrowed_at = datetime.now(timezone.utc).replace(microsecond=0)
    due_date = borrowed_at.date().fromordinal(
        borrowed_at.date().toordinal() + loan_days
    ).isoformat()
    cursor = db.execute(
        "INSERT INTO loans (book_id, member_id, borrowed_at, due_date) VALUES (?, ?, ?, ?)",
        (book_id, member_id, borrowed_at.isoformat(), due_date),
    )
    db.execute(
        "UPDATE books SET available_copies = available_copies - 1, updated_at = ? WHERE id = ?",
        (utc_now(), book_id),
    )
    db.commit()
    loan = db.execute(
        """
        SELECT l.*, b.title AS book_title, m.name AS member_name
        FROM loans l
        JOIN books b ON b.id = l.book_id
        JOIN members m ON m.id = l.member_id
        WHERE l.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return jsonify(row_to_dict(loan)), 201


@app.post("/api/loans/<loan_id>/return")
@handle_errors
def return_book(loan_id):
    loan_id = parse_id(loan_id, "loan_id")
    db = get_db()
    loan = db.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
    if not loan:
        return error("Loan not found.", 404)
    if loan["returned_at"]:
        return error("This loan has already been returned.", 409)
    db.execute(
        "UPDATE loans SET returned_at = ? WHERE id = ?", (utc_now(), loan_id)
    )
    db.execute(
        "UPDATE books SET available_copies = available_copies + 1, updated_at = ? WHERE id = ?",
        (utc_now(), loan["book_id"]),
    )
    db.commit()
    return jsonify(row_to_dict(db.execute(
        "SELECT * FROM loans WHERE id = ?", (loan_id,)
    ).fetchone()))


@app.get("/api/loans")
def list_loans():
    active = request.args.get("active")
    query = """
        SELECT l.*, b.title AS book_title, m.name AS member_name, m.email AS member_email
        FROM loans l
        JOIN books b ON b.id = l.book_id
        JOIN members m ON m.id = l.member_id
    """
    params = []
    if active in ("true", "false"):
        query += " WHERE l.returned_at IS NULL" if active == "true" else " WHERE l.returned_at IS NOT NULL"
    query += " ORDER BY l.borrowed_at DESC"
    rows = get_db().execute(query, params).fetchall()
    return jsonify({"loans": [row_to_dict(row) for row in rows], "count": len(rows)})


@app.get("/api/stats")
def stats():
    db = get_db()
    totals = db.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM books) AS books,
            (SELECT COALESCE(SUM(total_copies), 0) FROM books) AS total_copies,
            (SELECT COALESCE(SUM(available_copies), 0) FROM books) AS available_copies,
            (SELECT COUNT(*) FROM members WHERE active = 1) AS active_members,
            (SELECT COUNT(*) FROM loans WHERE returned_at IS NULL) AS active_loans
        """
    ).fetchone()
    return jsonify(row_to_dict(totals))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)