from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


class LibraryError(Exception):
    """Base exception for library domain errors."""


class ValidationError(LibraryError):
    """Raised when input data is invalid."""


class NotFoundError(LibraryError):
    """Raised when requested entity does not exist."""


class AlreadyExistsError(LibraryError):
    """Raised when trying to create an already existing entity."""


class BusinessRuleError(LibraryError):
    """Raised when a business rule is violated."""


@dataclass
class Book:
    book_id: str
    title: str
    author: str
    total_copies: int
    available_copies: int


@dataclass
class Reader:
    reader_id: str
    full_name: str


@dataclass
class Loan:
    book_id: str
    reader_id: str
    borrow_date: date
    due_date: date
    returned_date: date | None = None

    @property
    def is_active(self) -> bool:
        return self.returned_date is None


class LibraryManager:
    def __init__(self, fine_per_day: float = 1.0) -> None:
        if fine_per_day < 0:
            raise ValidationError("fine_per_day must be non-negative")

        self.fine_per_day = float(fine_per_day)
        self.books: dict[str, Book] = {}
        self.readers: dict[str, Reader] = {}
        self._active_loans: dict[tuple[str, str], Loan] = {}
        self._loan_history: list[Loan] = []

    @staticmethod
    def _require_non_empty(value: str, field_name: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValidationError(f"{field_name} must be non-empty")
        return normalized

    def add_book(self, book_id: str, title: str, author: str, total_copies: int) -> Book:
        book_id = self._require_non_empty(book_id, "book_id")
        title = self._require_non_empty(title, "title")
        author = self._require_non_empty(author, "author")

        if total_copies <= 0:
            raise ValidationError("total_copies must be greater than 0")
        if book_id in self.books:
            raise AlreadyExistsError(f"Book with id '{book_id}' already exists")

        book = Book(
            book_id=book_id,
            title=title,
            author=author,
            total_copies=total_copies,
            available_copies=total_copies,
        )
        self.books[book_id] = book
        return book

    def register_reader(self, reader_id: str, full_name: str) -> Reader:
        reader_id = self._require_non_empty(reader_id, "reader_id")
        full_name = self._require_non_empty(full_name, "full_name")

        if reader_id in self.readers:
            raise AlreadyExistsError(f"Reader with id '{reader_id}' already exists")

        reader = Reader(reader_id=reader_id, full_name=full_name)
        self.readers[reader_id] = reader
        return reader

    def get_book(self, book_id: str) -> Book:
        book_id = self._require_non_empty(book_id, "book_id")
        try:
            return self.books[book_id]
        except KeyError as exc:
            raise NotFoundError(f"Book with id '{book_id}' not found") from exc

    def get_reader(self, reader_id: str) -> Reader:
        reader_id = self._require_non_empty(reader_id, "reader_id")
        try:
            return self.readers[reader_id]
        except KeyError as exc:
            raise NotFoundError(f"Reader with id '{reader_id}' not found") from exc

    def search_books(self, query: str) -> list[Book]:
        normalized_query = self._require_non_empty(query, "query").lower()
        return [
            book
            for book in self.books.values()
            if normalized_query in book.title.lower() or normalized_query in book.author.lower()
        ]

    def borrow_book(self, book_id: str, reader_id: str, borrow_date: date, loan_days: int = 14) -> Loan:
        if loan_days <= 0:
            raise ValidationError("loan_days must be greater than 0")

        book = self.get_book(book_id)
        self.get_reader(reader_id)

        if book.available_copies <= 0:
            raise BusinessRuleError("No available copies for this book")

        key = (book.book_id, reader_id)
        if key in self._active_loans:
            raise BusinessRuleError("Reader already has this book on loan")

        loan = Loan(
            book_id=book.book_id,
            reader_id=reader_id,
            borrow_date=borrow_date,
            due_date=borrow_date + timedelta(days=loan_days),
        )
        self._active_loans[key] = loan
        self._loan_history.append(loan)
        book.available_copies -= 1
        return loan

    def return_book(self, book_id: str, reader_id: str, return_date: date) -> dict[str, float | int]:
        key = (self._require_non_empty(book_id, "book_id"), self._require_non_empty(reader_id, "reader_id"))
        loan = self._active_loans.get(key)
        if loan is None:
            raise BusinessRuleError("Active loan for this book and reader was not found")

        loan.returned_date = return_date
        self.books[loan.book_id].available_copies += 1
        del self._active_loans[key]

        overdue_days = max((return_date - loan.due_date).days, 0)
        fine_amount = round(overdue_days * self.fine_per_day, 2)
        return {"overdue_days": overdue_days, "fine_amount": fine_amount}

    def calculate_fine(self, due_date: date, return_date: date) -> float:
        overdue_days = max((return_date - due_date).days, 0)
        return round(overdue_days * self.fine_per_day, 2)

    def get_active_loans(self) -> list[Loan]:
        return list(self._active_loans.values())

    def get_reader_active_loans(self, reader_id: str) -> list[Loan]:
        reader_id = self._require_non_empty(reader_id, "reader_id")
        self.get_reader(reader_id)
        return [loan for loan in self._active_loans.values() if loan.reader_id == reader_id]

    def get_loan_history(self) -> list[Loan]:
        return list(self._loan_history)
