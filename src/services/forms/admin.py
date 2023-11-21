from .base import BaseForm, FormField


class AcceptNewUserForm(BaseForm):
    accept = FormField("✅ Принять")
    decline = FormField("❌ Отклонить")


class StartForm(BaseForm):
    accounting = FormField("📂 Бухгалтерия")
    reports = FormField("📂 Отчеты")
    other = FormField("📂 Другое")


class AccountingForm(BaseForm):
    set_misha_balance = FormField("👤 Изменить баланс Миши")
    users_salary = FormField("📈 Зарплата пользователей")
    charity = FormField("🫙 Благотвротельность")
    back = FormField("🔙 Назад")


class ReportsForm(BaseForm):
    user_reports = FormField("👤 Отчеты пользователя за период")
    partner_reports = FormField("👥 Отчеты по партнеру")
    statistic = FormField("📊 Статистика по отчетам")
    back = FormField("🔙 Назад")


class BalancesForm(BaseForm):
    common = FormField("💰 Общий баланс")
    misha = FormField("👤 Баланс Миши")
    business = FormField("💸 Баланс бизнеса")


class OtherForm(BaseForm):
    issue_balance = FormField("🔁 Выдать баланс")
    create_operation = FormField("➕ Создать операцию")
    get_operations = FormField("🧾 Получить операции")
    add_admin = FormField("➕ Админа")
    remove_admin = FormField("➖ Админа")
    remove_user = FormField("➖ Пользователя")
    set_currency = FormField("💱 Изменить валюту")
    manage_partners = FormField("👥 Управлять партнерами")
    back = FormField("🔙 Назад")


class ManagePartnersForm(BaseForm):
    add = FormField("➕ Партнера")
    remove = FormField("➖ Партнера")


class ManageSalaryForm(BaseForm):
    remove_user = FormField("👤 Снять у пользователя")
    set_user = FormField("🖌️ Изменить у пользователя")
    remove_everyone = FormField("👥 Снять у всех пользователей")


class SalaryPartnerForm(BaseForm):
    default = FormField("📊 Зарплата")
    bet20 = FormField("📈 Зарплата Бет 2.0")


class ManageCharityForm(BaseForm):
    statistic = FormField("📊 Статистика по благотворительности")
    report = FormField("📄 Отчет по благотворительности")


class DeleteReportForm(BaseForm):
    delete = FormField("Удалить отчет")


class ConfirmDeletionForm(BaseForm):
    no = FormField("Нет, оставить")
    yes = FormField("Да, удалить")


class RemoveCharityForm(BaseForm):
    remove = FormField("↪️ Снять все")


accept_new_user_form = AcceptNewUserForm()
start_form = StartForm()
accounting_form = AccountingForm()
reports_form = ReportsForm()
balances_form = BalancesForm()
other_form = OtherForm()
manage_partners_form = ManagePartnersForm()
manage_salary_form = ManageSalaryForm()
manage_charity_form = ManageCharityForm()
delete_report_form = DeleteReportForm()
confirm_deletion_form = ConfirmDeletionForm()
salary_partner_form = SalaryPartnerForm()
remove_charity_form = RemoveCharityForm()
