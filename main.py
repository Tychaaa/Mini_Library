from datetime import date

from library_manager import LibraryManager


def run() -> None:
    library = LibraryManager(fine_per_day=15.0)

    library.add_book("B-001", "Clean Code", "Robert C. Martin", total_copies=2)
    library.add_book("B-002", "The Pragmatic Programmer", "Andrew Hunt", total_copies=1)

    library.register_reader("R-001", "Ivan Petrov")
    library.register_reader("R-002", "Anna Sidorova")

    loan = library.borrow_book("B-001", "R-001", borrow_date=date(2026, 2, 1), loan_days=7)
    result = library.return_book("B-001", "R-001", return_date=date(2026, 2, 12))

    print("=== Mini Library ===")
    print(f"Borrowed: book={loan.book_id}, reader={loan.reader_id}, due={loan.due_date}")
    print(f"Returned with overdue days: {result['overdue_days']}")
    print(f"Fine amount: {result['fine_amount']}")

    found = library.search_books("pragmatic")
    print("Search result for 'pragmatic':", [book.title for book in found])


if __name__ == "__main__":
    run()
