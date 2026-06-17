# Personal Library

A desktop application for managing a personal book collection, built with Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey) ![Tkinter](https://img.shields.io/badge/UI-Tkinter-green)

---

## Features

- **Add & manage books** with title, author(s), publisher, subject, sub-subject, ISBN, edition, publication year, type (Physical/Electronic), and Dewey Decimal code
- **Searchable dropdowns** for authors, publishers, subjects, and sub-subjects — type to filter, or add a new entry inline without leaving the form
- **Browse and filter** the book list by subject and sub-subject
- **Manage reference data** — dedicated pages for Authors, Publishers, Subjects, and Sub-Subjects with add and delete support
- **Background image** that scales with the window, with semi-transparent overlay panels for readability

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Python Tkinter + ttk |
| ORM | SQLAlchemy (mapped_column / Mapped) |
| Database | SQLite |
| Image handling | Pillow (PIL) |

## Project Structure

```
main.py       — entry point, window setup
model.py      — SQLAlchemy ORM models (Book, Author, Publisher, Subject, SubCategory)
db.py         — all database queries and write operations
pages.py      — all UI pages and widgets
utils.py      — logging helper
```

## Getting Started

**Requirements:** Python 3.10+, pipenv

```bash
# Install dependencies
pipenv install

# Run the app
pipenv run python main.py
```

The SQLite database (`database.db`) is created automatically on first run.

## Data Model

- A **Book** can have multiple **Authors** (many-to-many), one **Publisher**, one **Subject**, and one **Sub-Subject**
- **Sub-Subjects** are scoped to a parent **Subject**
- All relationships use SQLAlchemy foreign keys with cascading deletes
