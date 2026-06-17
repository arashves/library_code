from sqlalchemy import select, delete

from model import Book, Subject, SubCategory, Author, Publisher


def get_all_books(session):
    return session.scalars(select(Book)).all()

def get_all_subjects(session):
    return session.scalars(select(Subject)).all()

def get_all_subcategories(session):
    return session.scalars(select(SubCategory)).all()

def get_subcategories_by_subject(session, subject_name):
    return session.scalars(
        select(SubCategory).join(SubCategory.subject).where(Subject.name == subject_name)
    ).all()

def get_all_authors(session):
    return session.scalars(select(Author).order_by(Author.last_name, Author.first_name)).all()

def get_all_publishers(session):
    return session.scalars(select(Publisher).order_by(Publisher.name)).all()


def get_subject_by_name(session, name):
    return session.scalars(select(Subject).where(Subject.name == name)).first()

def get_author_by_id(session, author_id):
    return session.get(Author, author_id)

def get_publisher_by_name(session, name):
    return session.scalars(select(Publisher).where(Publisher.name == name)).first()

def author_display_name(author):
    return f"{author.first_name} {author.last_name}"

def build_author_map(session):
    """Returns {display_name: author} for use in dropdowns."""
    authors = get_all_authors(session)
    return {author_display_name(a): a for a in authors}


def add_book(session, title, isbn, author, publisher_name,
             subject_name, subcategory_name,
             edition, publication_year, book_type, dewey_code):

    publisher = get_publisher_by_name(session, publisher_name) if publisher_name else None
    subject   = get_subject_by_name(session, subject_name) if subject_name else None

    subcategory = None
    if subcategory_name and subject:
        subcategory = session.scalars(
            select(SubCategory).where(
                SubCategory.name == subcategory_name,
                SubCategory.subject_id == subject.id
            )
        ).first()

    book = Book(
        title=title,
        isbn=isbn or None,
        edition=edition or None,
        publication_year=int(publication_year) if publication_year else None,
        book_type=book_type or None,
        dewey_code=dewey_code or None,
        authors=[author] if author else [],
        publisher=publisher,
        primary_subject=subject,
        subcategory_subject=subcategory,
    )
    session.add(book)
    session.commit()

def delete_book(session, book_id):
    session.execute(delete(Book).where(Book.universal_id == book_id))
    session.commit()


def add_subject(session, name):
    session.add(Subject(name=name))
    session.commit()

def delete_subject(session, subject_id):
    session.execute(delete(Subject).where(Subject.id == subject_id))
    session.commit()


def add_subcategory(session, subject, name):
    session.add(SubCategory(name=name, subject=subject))
    session.commit()

def delete_subcategory(session, subcategory_id):
    session.execute(delete(SubCategory).where(SubCategory.id == subcategory_id))
    session.commit()


def add_author(session, first_name, last_name, affiliation=None, wiki_link=None):
    session.add(Author(
        first_name=first_name,
        last_name=last_name,
        affiliation=affiliation or None,
        wiki_link=wiki_link or None,
    ))
    session.commit()

def delete_author(session, author_id):
    session.execute(delete(Author).where(Author.id == author_id))
    session.commit()


def add_publisher(session, name, country=None, website=None):
    session.add(Publisher(
        name=name,
        country=country or None,
        website=website or None,
    ))
    session.commit()

def delete_publisher(session, publisher_id):
    session.execute(delete(Publisher).where(Publisher.id == publisher_id))
    session.commit()
