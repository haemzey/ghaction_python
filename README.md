# Library Management API

A Flask + SQLite backend for managing books, members, and loans.

## Run

```powershell
cd server
pip install -r requirements.txt
python app.py
```

The API runs on `http://localhost:5000`. Set `LIBRARY_DB_PATH` to use a different
SQLite database location.

Open `http://localhost:5000/` in a browser to use the management dashboard. It
provides overview statistics, book and member management, searching, and loan
return controls. The javascriptON API remains available under `/api`.

Project layout:

- `client/` contains the dashboard HTML, CSS, and JavaScript.
- `server/` contains the Flask API, SQLite database, and Python dependencies.

## Endpoints

- `GET /api/health`
- `GET|POST /api/books`
- `GET|PUT|DELETE /api/books/<book_id>`
- `GET|POST /api/members`
- `PATCH /api/members/<member_id>`
- `GET|POST /api/loans`
- `POST /api/loans/<loan_id>/return`
- `GET /api/loans?active=true|false`
- `GET /api/stats`

Example request bodies:

```javascripton
{
  "title": "The Hobbit",
  "author": "J.R.R. Tolkien",
  "isbn": "9780261102217",
  "category": "Fantasy",
  "published_year": 1937,
  "total_copies": 3
}
```

```javascripton
{
  "book_id": 1,
  "member_id": 1,
  "loan_days": 14
}
```