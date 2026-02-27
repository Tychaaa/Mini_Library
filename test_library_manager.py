import unittest
from datetime import date

from library_manager import (
    BusinessRuleError,
    LibraryManager,
    NotFoundError,
    ValidationError,
)


class TestLibraryManager(unittest.TestCase):
    def setUp(self) -> None:
        self.library = LibraryManager(fine_per_day=10.0)
        self.library.add_book("B1", "Clean Code", "Robert Martin", total_copies=2)
        self.library.add_book("B2", "The Pragmatic Programmer", "Andrew Hunt", total_copies=1)
        self.library.register_reader("R1", "Ivan Petrov")
        self.library.register_reader("R2", "Anna Sidorova")

    def test_search_books_finds_match_by_title_case_insensitive(self) -> None:
        found = self.library.search_books("prAgMaTic")
        self.assertTrue(
            len(found) == 1 and found[0].book_id == "B2",
            f"Ожидалась одна книга B2 по названию, получено: {[book.book_id for book in found]}",
        )

    def test_search_books_finds_match_by_author(self) -> None:
        found = self.library.search_books("martin")
        self.assertTrue(
            len(found) == 1 and found[0].book_id == "B1",
            f"Ожидалась одна книга B1 по автору, получено: {[book.book_id for book in found]}",
        )

    def test_search_books_empty_query_raises_validation(self) -> None:
        with self.assertRaises(
            ValidationError,
            msg="Ожидался ValidationError для пустого поискового запроса",
        ):
            self.library.search_books("   ")

    def test_calculate_fine_returns_zero_without_overdue(self) -> None:
        fine = self.library.calculate_fine(due_date=date(2026, 4, 10), return_date=date(2026, 4, 10))
        self.assertTrue(
            fine == 0.0,
            f"Ожидался штраф 0.0 без просрочки, получено: {fine}",
        )

    def test_calculate_fine_returns_value_with_overdue(self) -> None:
        fine = self.library.calculate_fine(due_date=date(2026, 4, 10), return_date=date(2026, 4, 13))
        self.assertTrue(
            fine == 30.0,
            f"Ожидался штраф 30.0 при 3 днях просрочки, получено: {fine}",
        )

    def test_get_book_success_returns_correct_book(self) -> None:
        book = self.library.get_book("B1")
        self.assertTrue(
            book.title == "Clean Code",
            f"Ожидалось название 'Clean Code' для B1, получено: '{book.title}'",
        )

    def test_get_book_unknown_id_raises_not_found(self) -> None:
        with self.assertRaises(
            NotFoundError,
            msg="Ожидался NotFoundError для несуществующего book_id",
        ):
            self.library.get_book("UNKNOWN")

    def test_get_book_empty_id_raises_validation(self) -> None:
        with self.assertRaises(
            ValidationError,
            msg="Ожидался ValidationError для пустого book_id",
        ):
            self.library.get_book("   ")

    def test_return_book_without_active_loan_raises_business_error(self) -> None:
        with self.assertRaises(
            BusinessRuleError,
            msg="Ожидался BusinessRuleError при возврате без активной выдачи",
        ):
            self.library.return_book("B1", "R1", return_date=date(2026, 3, 5))

    def test_return_book_success_updates_state_and_returns_fine(self) -> None:
        self.library.borrow_book("B2", "R2", borrow_date=date(2026, 3, 1), loan_days=7)
        result = self.library.return_book("B2", "R2", return_date=date(2026, 3, 10))
        active_loans_count = len(self.library.get_active_loans())
        available = self.library.get_book("B2").available_copies
        self.assertTrue(
            result["overdue_days"] == 2 and result["fine_amount"] == 20.0 and active_loans_count == 0 and available == 1,
            f"Ожидались overdue_days=2, fine=20.0, active_loans=0, available=1; получено: result={result}, active_loans={active_loans_count}, available={available}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
