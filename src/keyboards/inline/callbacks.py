from aiogram.utils.callback_data import CallbackData

accept_new_user = CallbackData("accept_new_user", "id", "user_id")
select_partner = CallbackData("select_partner", "id")
select_user = CallbackData("select_user", "id")
confirm_report = CallbackData("confirm_report", "id")
select_currency = CallbackData("select_currency", "id")
delete_report = CallbackData("delte_report", "id", "report_id")
confirm_deletion = CallbackData("confirm_deletion", "id", "report_id")
