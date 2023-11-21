from .base import BaseForm, FormField


class StartForm(BaseForm):
    reports = FormField("🗒️ Мои отчеты")
    create_report = FormField("➕ Отчет")
    create_erroneous_report = FormField("➕ Ошибка")


class BalanceForm(BaseForm):
    balance = FormField("💰 Мой баланс")
    salary = FormField("💸 Моя зарплата")
    create_operation = FormField("➕ Создать операцию")
    charity = FormField("🧸 Благотворительность")


class ConfirmForm(BaseForm):
    accept = FormField("✅ Принять")
    reject = FormField("❌ Отклонить")


class TodayForm(BaseForm):
    today = FormField("За сегодня")


start_form = StartForm()
confirm_form = ConfirmForm()
balance_form = BalanceForm()
today_form = TodayForm()
