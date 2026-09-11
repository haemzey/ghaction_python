# Library Management System

A full-stack Library Management System built with **Python Flask**, **HTML/CSS/JavaScript**, **SQLite**, and **Docker**.

## Tech Stack

* **Backend:** Python, Flask, Gunicorn
* **Frontend:** HTML, CSS, JavaScript
* **Database:** SQLite
* **Web Server:** Nginx
* **Containerization:** Docker, Docker Compose
* **CI/CD:** GitHub Actions
* **Testing:** Pytest, Jest
* **Code Quality:** Pylint, ESLint, Stylelint, HTML Validate, Prettier
* **Security:** Gitleaks, Trivy
* **Registry:** Docker Hub

## Project Structure

```text
ghaction_python/
├── client/
│   ├── static/
│   │   ├── app.js
│   │   └── style.css
│   ├── templates/
│   │   └── index.html
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── package-lock.json
│
├── server/
│   ├── app.py
│   ├── test_app.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

## Features

* Book management
* Member management
* Book borrowing and returning
* Loan tracking
* Book search and filtering
* Library statistics
* REST API
* Automated testing
* Dockerized application
* Automated CI security checks

## Backend API

The Flask backend provides REST API endpoints for:

```text
GET    /api/health
GET    /api/books
POST   /api/books
GET    /api/books/<id>
PUT    /api/books/<id>
DELETE /api/books/<id>

GET    /api/members
POST   /api/members
PATCH  /api/members/<id>

POST   /api/loans
POST   /api/loans/<id>/return
GET    /api/loans

GET    /api/stats
```

## Run Locally

### Backend

```bash
cd server

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python app.py
```

The backend runs on:

```text
http://localhost:5000
```

### Run Tests

```bash
cd server
pytest -v
```

### Frontend

The frontend is served through Nginx in the Docker environment.

## Docker

Build and run the application with Docker Compose:

```bash
docker compose up --build
```

Stop the application:

```bash
docker compose down
```

The application can then be accessed through:

```text
http://localhost
```

## GitHub Actions

The project uses GitHub Actions to automate CI/CD.

The backend workflow validates changes under `server/` and performs:

```text
Lint → Test → Docker Build → Gitleaks → Trivy → Smoke Test
```

The frontend workflow validates changes under `client/` using:

```text
ESLint
Stylelint
HTML Validate
Prettier
Jest
```

### Security

**Gitleaks** scans the repository for accidentally committed secrets.

**Trivy** scans Docker images for vulnerabilities in:

* Operating system packages
* Application dependencies

![alt text](image-1.png)

