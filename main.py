
import csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal, InvalidOperation
from collections import defaultdict

DATA_FILE = Path(__file__).with_name("transactions.csv")
BUDGET_FILE = Path(__file__).with_name("category_budgets.csv")

FIELDS = ["id", "date", "type", "category", "amount", "description"]
BUDGET_FIELDS = ["category", "budget"]

CATEGORIES = [
    "Food", "Utilities", "Travel", "Education",
    "Shopping", "Health", "Salary", "Stipend",
    "Freelance", "Other"
]


# ---------- TRANSACTION FILE ----------

def setup_file():
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def load_data():
    setup_file()

    try:
        with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames != FIELDS:
                print("Error: CSV columns are incorrect.")
                return None

            records = list(reader)

        for record in records:
            datetime.strptime(record["date"], "%Y-%m-%d")
            amount = Decimal(record["amount"])

            if not amount.is_finite() or amount <= 0:
                raise ValueError("Invalid transaction amount.")

            if record["type"] not in ("Income", "Expense"):
                raise ValueError("Invalid transaction type.")

            int(record["id"])

        return records

    except (OSError, csv.Error, ValueError, KeyError,
            InvalidOperation, TypeError) as e:
        print("Could not read transaction data:", e)
        return None


def save_data(records):
    try:
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)
        return True

    except OSError as e:
        print("Could not save data:", e)
        return False


# ---------- ADD TRANSACTION ----------

def add_transaction():
    records = load_data()

    if records is None:
        return

    try:
        date_text = input(
            "Date YYYY-MM-DD (Enter for today): "
        ).strip()

        if not date_text:
            date_text = datetime.today().strftime("%Y-%m-%d")

        datetime.strptime(date_text, "%Y-%m-%d")

        kind = input("Type (Income/Expense): ").strip().title()

        if kind not in ("Income", "Expense"):
            print("Type must be Income or Expense.")
            return

        print("Categories:", ", ".join(CATEGORIES))
        category = input("Enter category: ").strip().title()

        if not category:
            print("Category cannot be empty.")
            return

        amount = Decimal(input("Enter amount: ").strip())

        if not amount.is_finite() or amount <= 0:
            print("Amount must be greater than zero.")
            return

        description = input("Description: ").strip()

        next_id = max(
            (int(r["id"]) for r in records),
            default=0
        ) + 1

        records.append({
            "id": str(next_id),
            "date": date_text,
            "type": kind,
            "category": category,
            "amount": str(amount.quantize(Decimal("0.01"))),
            "description": description
        })

        if save_data(records):
            print("Transaction added successfully!")

    except (ValueError, InvalidOperation):
        print("Invalid input. Check the date and amount.")


# ---------- VIEW TRANSACTIONS ----------

def view_transactions(records=None):
    if records is None:
        records = load_data()

    if records is None:
        return

    if not records:
        print("No transactions found.")
        return

    print("-" * 90)
    print(
        f"{'ID':<5}{'Date':<13}{'Type':<10}"
        f"{'Category':<16}{'Amount':>10}  Description"
    )
    print("-" * 90)

    for r in records:
        print(
            f"{r['id']:<5}{r['date']:<13}{r['type']:<10}"
            f"{r['category']:<16}"
            f"{Decimal(r['amount']):>10.2f}  "
            f"{r['description']}"
        )

    print("-" * 90)


# ---------- FINANCIAL SUMMARY ----------

def show_summary(records=None):
    if records is None:
        records = load_data()

    if records is None:
        return

    income = sum(
        (Decimal(r["amount"]) for r in records
         if r["type"] == "Income"),
        Decimal("0")
    )

    expenses = sum(
        (Decimal(r["amount"]) for r in records
         if r["type"] == "Expense"),
        Decimal("0")
    )

    print("\n========== FINANCIAL SUMMARY ==========")
    print(f"Total Income:   Rs. {income:.2f}")
    print(f"Total Expenses: Rs. {expenses:.2f}")
    print(f"Net Balance:    Rs. {income - expenses:.2f}")

    totals = defaultdict(lambda: Decimal("0"))

    for r in records:
        if r["type"] == "Expense":
            totals[r["category"]] += Decimal(r["amount"])

    print("\nExpenses by Category:")

    if not totals:
        print("No expenses recorded.")
    else:
        for category, amount in sorted(totals.items()):
            print(f"{category}: Rs. {amount:.2f}")

    print("=======================================")


# ---------- FILTER BY DATE ----------

def filter_by_date():
    records = load_data()

    if records is None:
        return

    try:
        start = datetime.strptime(
            input("Start date (YYYY-MM-DD): ").strip(),
            "%Y-%m-%d"
        ).date()

        end = datetime.strptime(
            input("End date (YYYY-MM-DD): ").strip(),
            "%Y-%m-%d"
        ).date()

        if start > end:
            print("Start date cannot be after end date.")
            return

        filtered = [
            r for r in records
            if start <= datetime.strptime(
                r["date"], "%Y-%m-%d"
            ).date() <= end
        ]

        view_transactions(filtered)
        show_summary(filtered)

    except ValueError:
        print("Invalid date. Use YYYY-MM-DD.")


# ---------- FILTER BY CATEGORY ----------

def filter_by_category():
    records = load_data()

    if records is None:
        return

    category = input("Enter category: ").strip().casefold()

    filtered = [
        r for r in records
        if r["category"].casefold() == category
    ]

    view_transactions(filtered)


# ---------- EXPORT CSV REPORT ----------

def export_report():
    records = load_data()

    if records is None:
        return

    filename = input(
        "Report filename (Enter for expense_report.csv): "
    ).strip() or "expense_report.csv"

    if (
        Path(filename).name != filename
        or not filename.lower().endswith(".csv")
    ):
        print("Please enter a simple CSV filename.")
        return

    try:
        report_path = Path(__file__).with_name(filename)

        with open(
            report_path, "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(records)

        print("Report exported successfully:", report_path)

    except OSError as e:
        print("Export failed:", e)


# ---------- BUDGET FILE ----------

def setup_budget_file():
    if not BUDGET_FILE.exists():
        with open(
            BUDGET_FILE, "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=BUDGET_FIELDS
            )
            writer.writeheader()


def read_budgets():
    setup_budget_file()

    budgets = {}

    with open(
        BUDGET_FILE, "r", newline="", encoding="utf-8"
    ) as f:
        reader = csv.DictReader(f)

        if reader.fieldnames != BUDGET_FIELDS:
            raise ValueError("Budget CSV columns are incorrect.")

        for row in reader:
            category = row["category"].strip().title()
            amount = Decimal(row["budget"])

            # Ignore old invalid category entries such as "1".
            if (
                category in CATEGORIES
                and amount.is_finite()
                and amount > 0
            ):
                budgets[category] = amount

    return budgets


def set_monthly_budget():
    print("\nAvailable categories:", ", ".join(CATEGORIES))
    category = input("Enter category: ").strip().title()

    if category not in CATEGORIES:
        print("Please enter a category from the list.")
        return

    try:
        budget = Decimal(
            input("Enter monthly budget (Rs.): ").strip()
        )

        if not budget.is_finite() or budget <= 0:
            print("Budget must be greater than zero.")
            return

        budgets = read_budgets()
        budgets[category] = budget.quantize(Decimal("0.01"))

        with open(
            BUDGET_FILE, "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=BUDGET_FIELDS
            )
            writer.writeheader()

            for name, amount in sorted(budgets.items()):
                writer.writerow({
                    "category": name,
                    "budget": str(amount)
                })

        print(
            f"Monthly budget set for {category}: "
            f"Rs. {budget:.2f}"
        )

    except (ValueError, InvalidOperation, OSError, csv.Error) as e:
        print("Could not set budget:", e)


# ---------- MONTHLY BUDGET STATUS ----------

def show_budget_status():
    records = load_data()

    if records is None:
        return

    try:
        budgets = read_budgets()
        current_month = datetime.today().strftime("%Y-%m")

        print(f"\n====== BUDGET STATUS: {current_month} ======")

        if not budgets:
            print("No valid budgets set. Choose option 7 first.")
            return

        for category, limit in sorted(budgets.items()):
            spent = sum(
                (
                    Decimal(r["amount"])
                    for r in records
                    if r["type"] == "Expense"
                    and r["category"].casefold() == category.casefold()
                    and r["date"].startswith(current_month)
                ),
                Decimal("0")
            )

            remaining = limit - spent

            print(f"\nCategory: {category}")
            print(f"Budget:   Rs. {limit:.2f}")
            print(f"Spent:    Rs. {spent:.2f}")

            if remaining < 0:
                print(
                    f"ALERT! Budget exceeded by "
                    f"Rs. {-remaining:.2f}"
                )
            elif remaining == 0:
                print("ALERT! You have reached your budget limit.")
            else:
                print(f"Remaining: Rs. {remaining:.2f}")

                if remaining <= limit * Decimal("0.20"):
                    print("Warning: You have used at least 80% of your budget.")

        print("=" * 40)

    except (OSError, csv.Error, ValueError, KeyError,
            InvalidOperation) as e:
        print("Could not read budget data:", e)


# ---------- SMART SAVINGS COACH ----------

def savings_coach():
    records = load_data()

    if records is None:
        return

    current_month = datetime.today().strftime("%Y-%m")

    monthly_records = [
        r for r in records
        if r["date"].startswith(current_month)
    ]

    income = sum(
        (
            Decimal(r["amount"])
            for r in monthly_records
            if r["type"] == "Income"
        ),
        Decimal("0")
    )

    expenses = sum(
        (
            Decimal(r["amount"])
            for r in monthly_records
            if r["type"] == "Expense"
        ),
        Decimal("0")
    )

    balance = income - expenses

    print("\n======= PENNYPILOT SAVINGS COACH =======")
    print("Month:", current_month)
    print(f"Income:   Rs. {income:.2f}")
    print(f"Expenses: Rs. {expenses:.2f}")
    print(f"Balance:  Rs. {balance:.2f}")

    if income == 0 and expenses == 0:
        print("\nNo transactions found for this month yet.")
        print("Add your income and expenses to get insights.")
        print("=======================================")
        return

    if income > 0:
        savings_rate = (balance / income) * Decimal("100")
        print(f"Savings rate: {savings_rate:.1f}%")

        if balance < 0:
            print("Tip: Your expenses exceed your income.")
            print("Review non-essential spending first.")
        elif savings_rate < 20:
            print("Tip: Try saving at least 20% of your income.")
        else:
            print("Great! You are maintaining a positive balance.")

    else:
        print("Tip: Record your income to calculate your savings rate.")

    category_totals = defaultdict(lambda: Decimal("0"))

    for r in monthly_records:
        if r["type"] == "Expense":
            category_totals[r["category"]] += Decimal(r["amount"])

    if category_totals:
        highest_category = max(
            category_totals,
            key=category_totals.get
        )

        print(
            f"\nHighest spending category: {highest_category} "
            f"(Rs. {category_totals[highest_category]:.2f})"
        )

        print("Tip: Review this category for possible savings.")

    try:
        budgets = read_budgets()

        for category, limit in budgets.items():
            spent = category_totals.get(category, Decimal("0"))

            if spent > limit:
                print(
                    f"Budget tip: Reduce {category} spending; "
                    f"you exceeded its budget by Rs. {spent - limit:.2f}."
                )

    except (OSError, csv.Error, ValueError,
            InvalidOperation, KeyError) as e:
        print("Budget insights unavailable:", e)

    print("=======================================")


# ---------- MAIN MENU ----------

def main():
    setup_file()
    setup_budget_file()

    while True:
        print("""
========== PENNYPILOT ==========
1. Add Income / Expense
2. View All Transactions
3. Financial Summary
4. Filter by Date Range
5. Filter by Category
6. Export CSV Report
7. Set Monthly Budget
8. View Budget Status
9. Smart Savings Coach
10. Exit
===============================
""")

        # Ask for the menu choice only ONCE.
        choice = input("Enter your choice (1-10): ").strip()

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_transactions()
        elif choice == "3":
            show_summary()
        elif choice == "4":
            filter_by_date()
        elif choice == "5":
            filter_by_category()
        elif choice == "6":
            export_report()
        elif choice == "7":
            set_monthly_budget()
        elif choice == "8":
            show_budget_status()
        elif choice == "9":
            savings_coach()
        elif choice == "10":
            print("Thank you for using PennyPilot!")
            break
        else:
            print("Invalid choice. Enter a number from 1 to 10.")


if __name__ == "__main__":
    main()
