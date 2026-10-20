import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


class Account:
    """Базовий клас банківського рахунку."""

    def __init__(self, balance: float, pin: str, iban: Optional[str] = None, currency: str = "UAH"):
        self.iban = iban if iban else self._generate_iban()
        self.currency = currency.upper()
        self._balance = float(balance)
        self._pin = str(pin)
        self.failed_pin_attempts = 0
        self.is_blocked = False

    @staticmethod
    def _generate_iban() -> str:
        random_digits = "".join([str(random.randint(0, 9)) for _ in range(18)])
        return f"UA8930000100000{random_digits}"

    @property
    def balance(self) -> float:
        return self._balance

    def verify_pin(self, entered_pin: str) -> bool:
        if self.is_blocked:
            return False

        if self._pin == str(entered_pin):
            self.failed_pin_attempts = 0
            return True

        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= 3:
            self.is_blocked = True
        return False

    def change_pin(self, old_pin: str, new_pin: str) -> Tuple[bool, str]:
        """Зміна PIN-коду."""
        if not self.verify_pin(old_pin):
            return False, "Старий PIN-код невірний."
        if not new_pin.isdigit() or len(new_pin) != 4:
            return False, "Новий PIN-код має складатися з 4 цифр."
        
        self._pin = str(new_pin)
        return True, "PIN-код успішно змінено!"

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or amount > self._balance:
            return False
        self._balance -= amount
        return True

    def deposit(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self._balance += amount
        return True

    def get_info(self) -> str:
        status = " [ЗАБЛОКОВАНО]" if self.is_blocked else ""
        return f"Звичайний рахунок | IBAN: {self.iban} | Баланс: {self._balance:.2f} {self.currency}{status}"


class SavingsAccount(Account):
    """Накопичувальний рахунок."""

    def __init__(self, balance: float, percent: float, pin: str, iban: Optional[str] = None, currency: str = "UAH"):
        super().__init__(balance, pin, iban, currency)
        self.percent = percent
        self.min_balance = 100.0

    def add_percent(self) -> float:
        bonus = self._balance * (self.percent / 100)
        self._balance += bonus
        return bonus

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or (self._balance - amount) < self.min_balance:
            return False
        self._balance -= amount
        return True

    def get_info(self) -> str:
        status = " [ЗАБЛОКОВАНО]" if self.is_blocked else ""
        return (f"Накопичувальний ({self.percent}%) | "
                f"IBAN: {self.iban} | Баланс: {self._balance:.2f} {self.currency}{status}")


class DepositAccount(Account):
    """Депозитний рахунок із терміном дії 1 місяць та штрафом за дострокове зняття."""

    def __init__(self, balance: float, percent: float, term_days: int = 30, pin: str = "1234", iban: Optional[str] = None, currency: str = "UAH"):
        super().__init__(balance, pin, iban, currency)
        self.percent = percent
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=term_days)
        self.early_withdrawal_penalty = 0.10
        self.is_matured = False

    def is_expired(self) -> bool:
        return datetime.now() >= self.end_date

    def withdraw(self, amount: float) -> bool:
        if amount <= 0:
            return False

        if not self.is_expired():
            penalty = amount * self.early_withdrawal_penalty
            total_needed = amount + penalty
            if total_needed > self._balance:
                return False
            self._balance -= total_needed
            return True

        if amount > self._balance:
            return False
        self._balance -= amount
        return True

    def payout_interest(self) -> Tuple[bool, float]:
        if not self.is_expired():
            return False, 0.0
        if self.is_matured:
            return False, 0.0

        bonus = self._balance * (self.percent / 100)
        self._balance += bonus
        self.is_matured = True
        return True, bonus

    def get_info(self) -> str:
        status = " [ЗАБЛОКОВАНО]" if self.is_blocked else ""
        expired_str = "Завершено" if self.is_expired() else f"До {self.end_date.strftime('%Y-%m-%d')}"
        return (f"Депозит на 1 міс ({self.percent}%, {expired_str}) | "
                f"IBAN: {self.iban} | Баланс: {self._balance:.2f} {self.currency}{status}")


class GoalAccount(Account):
    """Скарбничка / Ціль накопичення."""

    def __init__(self, goal_title: str, target_amount: float, balance: float, pin: str, iban: Optional[str] = None, currency: str = "UAH"):
        super().__init__(balance, pin, iban, currency)
        self.goal_title = goal_title
        self.target_amount = float(target_amount)

    def get_progress(self) -> float:
        if self.target_amount <= 0:
            return 100.0
        return min((self._balance / self.target_amount) * 100, 100.0)

    def get_info(self) -> str:
        status = " [ЗАБЛОКОВАНО]" if self.is_blocked else ""
        progress = self.get_progress()
        return (f"Скарбничка '{self.goal_title}' ({progress:.1f}% з {self.target_amount:.2f}) | "
                f"IBAN: {self.iban} | Баланс: {self._balance:.2f} {self.currency}{status}")


class CreditAccount(Account):
    """Кредитний рахунок."""

    def __init__(self, balance: float, credit_limit: float, pin: str, iban: Optional[str] = None, currency: str = "UAH"):
        super().__init__(balance, pin, iban, currency)
        self.credit_limit = float(credit_limit)

    def withdraw(self, amount: float) -> bool:
        if amount <= 0 or (self._balance - amount) < -self.credit_limit:
            return False
        self._balance -= amount
        return True

    def get_info(self) -> str:
        status = " [ЗАБЛОКОВАНО]" if self.is_blocked else ""
        return (f"Кредитний (Ліміт: {self.credit_limit:.2f}) | "
                f"IBAN: {self.iban} | Баланс: {self._balance:.2f} {self.currency}{status}")


class Client:
    """Клас клієнта банку."""

    def __init__(self, name: str):
        self.name = name
        self.accounts: List[Account] = []

    def add_account(self, account: Account):
        self.accounts.append(account)

    def get_account_by_currency(self, currency: str) -> Optional[Account]:
        """Пошук звичайного рахунку у вказаній валюті."""
        for acc in self.accounts:
            if type(acc) is Account and acc.currency == currency.upper():
                return acc
        return None


class Transaction:
    """Запис про транзакцію."""

    def __init__(self, sender: str, receiver: str, amount: float, status: str, currency: str = "UAH"):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.currency = currency
        self.status = status
        self.date = datetime.now()

    def __str__(self) -> str:
        return f"[{self.date.strftime('%Y-%m-%d %H:%M:%S')}] {self.sender} -> {self.receiver} | {self.amount:.2f} {self.currency} | {self.status}"


class RecurringPayment:
    """Регулярний платіж."""

    def __init__(self, sender_iban: str, receiver_iban: str, amount: float, days_interval: int, title: str):
        self.sender_iban = sender_iban
        self.receiver_iban = receiver_iban
        self.amount = amount
        self.days_interval = days_interval
        self.title = title
        self.next_execution = datetime.now() + timedelta(days=days_interval)
        self.is_active = True

    def update_next_execution(self):
        self.next_execution += timedelta(days=self.days_interval)


class Bank:
    """Ядро банківської системи."""

    def __init__(self, transfer_fee_rate: float = 0.01):
        self.accounts: Dict[str, Account] = {}
        self.clients: List[Client] = []
        self.transactions: List[Transaction] = []
        self.recurring_payments: List[RecurringPayment] = []
        self.transfer_fee_rate = transfer_fee_rate

        self.exchange_rates = {
            "UAH": 1.0,
            "USD": 41.50,
            "EUR": 45.20
        }

    def get_exchange_rates_info(self) -> str:
        usd_rate = self.exchange_rates["USD"]
        eur_rate = self.exchange_rates["EUR"]
        eur_usd = eur_rate / usd_rate

        info = (
            "\n--- КУРСИ ВАЛЮТ БАНКУ (за 1 одиницю) ---\n"
            f"1 USD = {usd_rate:.2f} UAH\n"
            f"1 EUR = {eur_rate:.2f} UAH\n"
            f"1 EUR = {eur_usd:.2f} USD\n"
            f"1 UAH = {1/usd_rate:.4f} USD | {1/eur_rate:.4f} EUR\n"
            "---------------------------------------"
        )
        return info

    def convert_currency(self, amount: float, from_curr: str, to_curr: str) -> float:
        if from_curr == to_curr:
            return amount
        amount_in_uah = amount * self.exchange_rates.get(from_curr, 1.0)
        return amount_in_uah / self.exchange_rates.get(to_curr, 1.0)

    def add_client(self, client: Client):
        self.clients.append(client)
        for acc in client.accounts:
            self.accounts[acc.iban] = acc

    def get_client_by_name(self, name: str) -> Optional[Client]:
        for client in self.clients:
            if client.name.lower() == name.lower():
                return client
        return None

    def get_account_history(self, iban: str) -> List[Transaction]:
        return [t for t in self.transactions if t.sender == iban or t.receiver == iban]

    def atm_deposit(self, iban: str, amount: float) -> Tuple[bool, str]:
        account = self.accounts.get(iban)
        if not account:
            return False, "Рахунок не знайдено."
        if amount <= 0:
            return False, "Некоректна сума."

        if account.deposit(amount):
            self.transactions.append(Transaction("Поповнення", iban, amount, "Успішно", account.currency))
            return True, f"Рахунок поповнено на {amount:.2f} {account.currency}."
        return False, "Помилка поповнення."

    def atm_withdraw(self, iban: str, amount: float, pin: str) -> Tuple[bool, str]:
        account = self.accounts.get(iban)
        if not account:
            return False, "Рахунок не знайдено."

        if not account.verify_pin(pin):
            self.transactions.append(Transaction(iban, "Зняття", 0, "Відхилено (Невірний PIN)", account.currency))
            if account.is_blocked:
                return False, "Рахунок заблоковано!"
            return False, "Невірний PIN-код."

        if isinstance(account, DepositAccount) and not account.is_expired():
            print("УВАГА: Депозит ще не завершено! Дострокове зняття передбачає штраф 10%.")

        if account.withdraw(amount):
            self.transactions.append(Transaction(iban, "Зняття", amount, "Успішно", account.currency))
            return True, f"Заберіть ваші {amount:.2f} {account.currency}."

        self.transactions.append(Transaction(iban, "Зняття", amount, "Відхилено", account.currency))
        return False, "Недостатньо коштів або порушено ліміти."

    def transfer(self, sender_iban: str, receiver_iban: str, amount: float, pin: str) -> Tuple[bool, str]:
        if sender_iban == receiver_iban:
            return False, "Переказ на той самий рахунок заборонено."

        sender_acc = self.accounts.get(sender_iban)
        receiver_acc = self.accounts.get(receiver_iban)

        if not sender_acc or not receiver_acc:
            return False, "Рахунок відправника або отримувача не знайдено."

        if isinstance(sender_acc, GoalAccount):
            return False, "Зі скарбнички не можна робити перекази. Дозволено тільки зняття коштів!"

        if not sender_acc.verify_pin(pin):
            self.transactions.append(Transaction(sender_iban, receiver_iban, amount, "Відхилено (Невірний PIN)", sender_acc.currency))
            if sender_acc.is_blocked:
                return False, "Рахунок заблоковано!"
            return False, "Невірний PIN-код."

        fee = amount * self.transfer_fee_rate
        total_amount = amount + fee

        if isinstance(sender_acc, DepositAccount) and not sender_acc.is_expired():
            print("УВАГА: Зняття з депозиту достроково передбачає штраф 10%.")

        if sender_acc.withdraw(total_amount):
            received_amount = self.convert_currency(amount, sender_acc.currency, receiver_acc.currency)
            receiver_acc.deposit(received_amount)

            self.transactions.append(Transaction(sender_iban, receiver_iban, amount, "Успішно", sender_acc.currency))
            msg = f"Переказ успішний (комісія: {fee:.2f} {sender_acc.currency})."
            if sender_acc.currency != receiver_acc.currency:
                msg += f" Зараховано отримувачу: {received_amount:.2f} {receiver_acc.currency}."
            return True, msg

        self.transactions.append(Transaction(sender_iban, receiver_iban, amount, "Відхилено", sender_acc.currency))
        return False, "Недостатньо коштів з урахуванням комісії."

    def exchange_currency_by_target(self, client: Client, sender_acc: Account, target_currency: str, amount: float, pin: str) -> Tuple[bool, str]:
        """Обмін валюти із вибором конкретної цільової валюти."""
        target_currency = target_currency.upper()

        if isinstance(sender_acc, GoalAccount):
            return False, "Скарбничка не підтримує обмін валюти."

        if sender_acc.currency == target_currency:
            return False, f"Ваш рахунок вже у валюті {target_currency}! Виберіть іншу валюту."

        if target_currency not in self.exchange_rates:
            return False, "Така валюта не підтримується банком."

        if not sender_acc.verify_pin(pin):
            self.transactions.append(Transaction(sender_acc.iban, "Обмін", amount, "Відхилено (PIN)", sender_acc.currency))
            return False, "Невірний PIN-код."

        # Пошук або створення рахунку у цільовій валюті для клієнта
        receiver_acc = client.get_account_by_currency(target_currency)
        if not receiver_acc:
            receiver_acc = Account(balance=0.0, pin=pin, currency=target_currency)
            client.add_account(receiver_acc)
            self.accounts[receiver_acc.iban] = receiver_acc
            print(f"-> Автоматично відкрито новий рахунок у {target_currency} (IBAN: {receiver_acc.iban})")

        converted_amount = self.convert_currency(amount, sender_acc.currency, target_currency)

        if sender_acc.withdraw(amount):
            receiver_acc.deposit(converted_amount)
            self.transactions.append(
                Transaction(sender_acc.iban, receiver_acc.iban, amount, f"Обмін {sender_acc.currency} -> {target_currency}", sender_acc.currency)
            )
            return True, f"Успішно обміняно {amount:.2f} {sender_acc.currency} на {converted_amount:.2f} {target_currency}."

        return False, "Недостатньо коштів для виконання обміну."

    def add_recurring_payment(self, sender_iban: str, receiver_iban: str, amount: float, interval_days: int, title: str) -> Tuple[bool, str]:
        if receiver_iban not in self.accounts:
            return False, "Рахунок отримувача не знайдено."
        if amount <= 0 or interval_days <= 0:
            return False, "Некоректні параметри платежу."

        sender_acc = self.accounts.get(sender_iban)
        if isinstance(sender_acc, GoalAccount):
            return False, "Зі скарбнички не можна створювати регулярні платежі."

        payment = RecurringPayment(sender_iban, receiver_iban, amount, interval_days, title)
        self.recurring_payments.append(payment)
        return True, f"Платіж '{title}' створено. Наступне виконання: {payment.next_execution.strftime('%Y-%m-%d')}."

    def process_recurring_payments(self) -> List[str]:
        now = datetime.now()
        logs = []

        for p in self.recurring_payments:
            if p.is_active and now >= p.next_execution:
                sender_acc = self.accounts.get(p.sender_iban)
                receiver_acc = self.accounts.get(p.receiver_iban)

                if sender_acc and receiver_acc:
                    received_amount = self.convert_currency(p.amount, sender_acc.currency, receiver_acc.currency)
                    if sender_acc.withdraw(p.amount):
                        receiver_acc.deposit(received_amount)
                        self.transactions.append(Transaction(p.sender_iban, p.receiver_iban, p.amount, f"Регулярний: {p.title}", sender_acc.currency))
                        p.update_next_execution()
                        logs.append(f"Виконано: '{p.title}' на суму {p.amount:.2f} {sender_acc.currency}")
                    else:
                        self.transactions.append(Transaction(p.sender_iban, p.receiver_iban, p.amount, f"Регулярний відхилено: {p.title}", sender_acc.currency))
                        logs.append(f"Відхилено (недостатньо коштів): '{p.title}'")
        return logs


# --- Консольний інтерфейс (CLI) ---

def prompt_float(message: str) -> Optional[float]:
    try:
        return float(input(message))
    except ValueError:
        print("Помилка: введене значення має бути числом.")
        return None


def handle_account_operations(bank: Bank, client: Client, account: Account):
    while True:
        print(f"\n--- Операції для {account.iban} ({account.currency}) ---")
        
        if isinstance(account, GoalAccount):
            print("1. Поповнити скарбничку")
            print("2. Зняти кошти зі скарбнички")
            print("3. Перевірити баланс та прогрес цілі")
            print("4. Переглянути історію")
            print("5. Змінити PIN-код")
            print("0. Назад")

            op = input("Оберіть дію: ").strip()

            if op == "1":
                amount = prompt_float(f"Введіть суму поповнення ({account.currency}): ")
                if amount is not None:
                    _, msg = bank.atm_deposit(account.iban, amount)
                    print(msg)

            elif op == "2":
                pin = input("Введіть PIN: ")
                amount = prompt_float(f"Введіть суму для зняття ({account.currency}): ")
                if amount is not None:
                    _, msg = bank.atm_withdraw(account.iban, amount, pin)
                    print(msg)

            elif op == "3":
                print(f"Поточний баланс: {account.balance:.2f} {account.currency}")
                print(f"Прогрес цілі '{account.goal_title}': {account.get_progress():.1f}% з {account.target_amount:.2f} {account.currency}")

            elif op == "4":
                history = bank.get_account_history(account.iban)
                print("\nІсторія транзакцій:" if history else "Транзакцій не знайдено.")
                for t in history:
                    print(t)

            elif op == "5":
                old_pin = input("Введіть поточний PIN: ")
                new_pin = input("Введіть новий 4-значний PIN: ")
                _, msg = account.change_pin(old_pin, new_pin)
                print(msg)

            elif op == "0":
                break

        else:
            print("1. Поповнити (банкомат)")
            print("2. Зняти готівку")
            print("3. Зробити звичайний переказ")
            print("4. ОБМІНЯТИ ВАЛЮТУ")
            print("5. Налаштувати регулярний платіж")
            print("6. Перевірити баланс")
            print("7. Переглянути історію")
            print("8. Змінити PIN-код")

            if isinstance(account, SavingsAccount):
                print("9. Нарахувати відсотки (накопичувальний)")
            elif isinstance(account, DepositAccount):
                print("9. Виплатити відсотки за депозитом (якщо термін закінчився)")

            print("0. Назад")

            op = input("Оберіть дію: ").strip()

            if op == "1":
                amount = prompt_float(f"Введіть суму ({account.currency}): ")
                if amount is not None:
                    _, msg = bank.atm_deposit(account.iban, amount)
                    print(msg)

            elif op == "2":
                pin = input("Введіть PIN: ")
                amount = prompt_float(f"Введіть суму ({account.currency}): ")
                if amount is not None:
                    _, msg = bank.atm_withdraw(account.iban, amount, pin)
                    print(msg)

            elif op == "3":
                receiver_iban = input("Введіть IBAN отримувача: ").strip()
                amount = prompt_float(f"Введіть суму ({account.currency}): ")
                if amount is not None:
                    pin = input("Введіть PIN для підтвердження: ")
                    _, msg = bank.transfer(account.iban, receiver_iban, amount, pin)
                    print(msg)

            elif op == "4":
                print(bank.get_exchange_rates_info())
                print(f"Поточна валюта списання: {account.currency}")
                
                target_currency = input("Введіть валюту, ЯКУ ВИ ХОЧЕТЕ КУПИТИ (USD / EUR / UAH): ").strip().upper()
                amount = prompt_float(f"Введіть суму для обміну ({account.currency}): ")
                
                if amount is not None:
                    pin = input("Введіть PIN для підтвердження обміну: ")
                    _, msg = bank.exchange_currency_by_target(client, account, target_currency, amount, pin)
                    print(msg)

            elif op == "5":
                receiver_iban = input("Введіть IBAN отримувача: ").strip()
                amount = prompt_float(f"Введіть суму ({account.currency}): ")
                try:
                    days = int(input("Інтервал у днях: "))
                    title = input("Назва платежу: ").strip()
                    if amount is not None:
                        _, msg = bank.add_recurring_payment(account.iban, receiver_iban, amount, days, title)
                        print(msg)
                except ValueError:
                    print("Помилка: інтервал має бути цілим числом.")

            elif op == "6":
                print(f"Поточний баланс: {account.balance:.2f} {account.currency}")

            elif op == "7":
                history = bank.get_account_history(account.iban)
                print("\nІсторія транзакцій:" if history else "Транзакцій не знайдено.")
                for t in history:
                    print(t)

            elif op == "8":
                old_pin = input("Введіть поточний PIN: ")
                new_pin = input("Введіть новий 4-значний PIN: ")
                _, msg = account.change_pin(old_pin, new_pin)
                print(msg)

            elif op == "9" and isinstance(account, SavingsAccount):
                bonus = account.add_percent()
                print(f"Нараховано відсотки: {bonus:.2f} {account.currency}")

            elif op == "9" and isinstance(account, DepositAccount):
                success, bonus = account.payout_interest()
                if success:
                    print(f"Депозит виплачено! Нараховано відсотків: {bonus:.2f} {account.currency}")
                else:
                    print("Термін депозиту (1 місяць) ще не закінчився або відсотки вже виплачені.")

            elif op == "0":
                break

        if input("\nПродовжити роботу з цим рахунком? (так/ні): ").strip().lower() not in ["так", "yes", "y"]:
            break


def main():
    bank = Bank()

    # Ініціалізація клієнтів
    client1 = Client("Максим")
    client2 = Client("Ілля")

    # Рахунки Максима
    client1.add_account(Account(balance=10000, pin="1234", iban="UA893000010000011111111111111", currency="UAH"))
    client1.add_account(SavingsAccount(balance=500, percent=5, pin="1234", iban="UA893000010000022222222222222", currency="UAH"))
    client1.add_account(GoalAccount(goal_title="На новий ноутбук", target_amount=40000, balance=12500, pin="1234", iban="UA893000010000066666666666666", currency="UAH"))
    client1.add_account(DepositAccount(balance=20000, percent=12.5, term_days=30, pin="1234", iban="UA893000010000077777777777777", currency="UAH"))

    # Рахунки Іллі
    client2.add_account(Account(balance=15000, pin="5678", iban="UA893000010000033333333333333", currency="UAH"))
    client2.add_account(Account(balance=1200, pin="5678", iban="UA893000010000044444444444444", currency="USD"))
    client2.add_account(CreditAccount(balance=300, credit_limit=1500, pin="5678", iban="UA893000010000055555555555555", currency="EUR"))

    bank.add_client(client1)
    bank.add_client(client2)

    bank.process_recurring_payments()

    while True:
        print("\n==========================================")
        print("          БАНКІВСЬКА СИСТЕМА              ")
        print("==========================================")
        print("1. Обрати клієнта")
        print("2. Переглянути поточні курси валют")
        print("0. Вийти")

        choice = input("Оберіть дію: ").strip()

        if choice == "0":
            print("\nРоботу завершено.")
            break
        elif choice == "2":
            print(bank.get_exchange_rates_info())
            continue
        elif choice != "1":
            print("Некоректний вибір.")
            continue

        client_name = input("\nВведіть ім'я клієнта: ").strip()
        client = bank.get_client_by_name(client_name)

        if not client:
            print("Клієнта не знайдено.")
            continue

        print(f"\nКлієнт: {client.name}")
        for idx, acc in enumerate(client.accounts, 1):
            print(f"  {idx}. {acc.get_info()}")

        try:
            acc_choice = int(input("Оберіть номер рахунку: ")) - 1
            if 0 <= acc_choice < len(client.accounts):
                handle_account_operations(bank, client, client.accounts[acc_choice])
            else:
                print("Некоректний номер рахунку.")
        except ValueError:
            print("Будь ласка, введіть число.")


if __name__ == "__main__":
    main()