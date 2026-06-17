import os
from utils import Alogger

from typing import List, Optional
from sqlalchemy import Integer, String, ForeignKey, Table, Column, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

alogger = Alogger("model")

class Base(DeclarativeBase):
    pass

association_table_1 = Table(
    "association_table_1",
    Base.metadata,
    Column("l_id", ForeignKey("book.universal_id"), primary_key=True),
    Column("r_id", ForeignKey("author.id"), primary_key=True),
)

class Book(Base):
    __tablename__ = "book"

    universal_id:           Mapped[int]                         = mapped_column(primary_key=True)
    title:                  Mapped[str]                         = mapped_column(nullable=False)
    isbn:                   Mapped[Optional[str]]               = mapped_column(nullable=True)
    edition:                Mapped[Optional[str]]               = mapped_column(nullable=True)
    publication_year:       Mapped[Optional[int]]               = mapped_column(nullable=True)
    book_type:              Mapped[Optional[str]]               = mapped_column(nullable=True)
    dewey_code:             Mapped[Optional[str]]               = mapped_column(nullable=True)

    authors:                Mapped[List["Author"]]              = relationship(back_populates="book", secondary=association_table_1)

    publisher_id:           Mapped[Optional[int]]               = mapped_column(ForeignKey("publishers.id"))
    publisher:              Mapped[Optional["Publisher"]]       = relationship(back_populates="book")

    primary_subject_id:     Mapped[Optional[int]]               = mapped_column(ForeignKey("subject.id"))
    primary_subject:        Mapped[Optional["Subject"]]         = relationship(back_populates="book")

    subcategory_subject_id: Mapped[Optional[int]]               = mapped_column(ForeignKey("subcategory.id"))
    subcategory_subject:    Mapped[Optional["SubCategory"]]     = relationship(back_populates="book")


class Subject(Base):
    __tablename__ = "subject"

    id:                     Mapped[int]                 = mapped_column(primary_key=True)
    name:                   Mapped[str]                 = mapped_column(nullable=False)

    book:                   Mapped[List["Book"]]        = relationship(back_populates="primary_subject", cascade="all")
    subcategories:          Mapped[List["SubCategory"]] = relationship(back_populates="subject", cascade="all")

class SubCategory(Base):
    __tablename__ = "subcategory"

    id:                     Mapped[int]                 = mapped_column(primary_key=True)
    name:                   Mapped[str]                 = mapped_column(nullable=False)

    subject_id:             Mapped[Optional[int]]       = mapped_column(ForeignKey("subject.id"))
    subject:                Mapped[Optional["Subject"]] = relationship(back_populates="subcategories")

    book:                   Mapped[List["Book"]]        = relationship(back_populates="subcategory_subject", cascade="all")

class Author(Base):
    __tablename__ = "author"

    id:             Mapped[int]           = mapped_column(primary_key=True)
    first_name:     Mapped[str]           = mapped_column(nullable=False)
    last_name:      Mapped[str]           = mapped_column(nullable=False)
    affiliation:    Mapped[Optional[str]] = mapped_column(nullable=True)
    wiki_link:      Mapped[Optional[str]] = mapped_column(nullable=True)

    book:           Mapped[List["Book"]]  = relationship(back_populates="authors", secondary=association_table_1)

class Publisher(Base):
    __tablename__ = "publishers"

    id:       Mapped[int]           = mapped_column(primary_key=True)
    name:     Mapped[str]           = mapped_column(nullable=False)
    country:  Mapped[Optional[str]] = mapped_column(nullable=True)
    website:  Mapped[Optional[str]] = mapped_column(nullable=True)

    book:     Mapped[List["Book"]]  = relationship(back_populates="publisher", cascade="all")


def create_all(engine):
    Base.metadata.create_all(engine)
    alogger.debug("Tables created")

def drop_all(engine):
    Base.metadata.drop_all(engine)
    alogger.debug("Tables deleted")


def init():
    directory = (str(os.getcwd()) + "\\" )
    sqlite_path = ("sqlite:///"+directory+"\\database.db")
    sqlite_path = sqlite_path.replace("\\","\\\\")
    engine = create_engine(sqlite_path, echo=False)
    Session = sessionmaker(engine)
    session = Session()
    session.begin()
    conn = engine.connect()
    if engine.dialect.has_table(conn, table_name="book"):
        pass
    else:
        create_all(engine)

    alogger.debug("The DB initiated")

    return session
