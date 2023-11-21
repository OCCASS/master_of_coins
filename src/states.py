from aiogram.dispatcher.filters.state import State
from aiogram.dispatcher.filters.state import StatesGroup


class States(StatesGroup):
    class UserReports(StatesGroup):
        date = State()

    class CreateReport(StatesGroup):
        photo = State()
        amount = State()
        refund_amount = State()
        partner = State()
        salary_percent = State()
        confirm = State()

    class CreateOperation(StatesGroup):
        amount = State()
        reason = State()

    class Admin(StatesGroup):
        class Accounting(StatesGroup):
            class SetMishaBalance(StatesGroup):
                user = State()
                amount = State()

            class RemoveUserSalary(StatesGroup):
                user = State()

            class SetUserSalary(StatesGroup):
                user = State()
                amount = State()

            class ChairtyReport(StatesGroup):
                date = State()

        class Reports(StatesGroup):
            class User(StatesGroup):
                user = State()
                date = State()

            class Partner(StatesGroup):
                partner = State()
                date = State()

            class Statistic(StatesGroup):
                date = State()

        class Other(StatesGroup):
            class IssueBalance(StatesGroup):
                user = State()
                amount = State()

            class Operations(StatesGroup):
                date = State()

            class AddAdmin(StatesGroup):
                user = State()

            class RemoveAdmin(StatesGroup):
                user = State()

            class RemoveUser(StatesGroup):
                user = State()

            class SetCurrency(StatesGroup):
                user = State()
                currency = State()

            class ManagePartners(StatesGroup):
                action = State()

                class Add(StatesGroup):
                    name = State()

                class Remove(StatesGroup):
                    partner = State()
