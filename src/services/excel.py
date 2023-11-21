import datetime
from pathlib import Path
from typing import Sequence
import pandas as pd

from src.data import settings
from src.services.database.models import Report, User, Partner


async def create_reports_excel(reports: Sequence[Report]) -> Path:
    data = []
    for r in reports:
        user = await User.get(id=r.user)
        partner = await Partner.get(id=r.partner)
        data.append(
            {
                "Дата и время": r.created_at.strftime("%d.%m.%Y %H:%M:%S"),
                "Имя пользователя": user.username,
                "Сумма ставки": f"{r.amount}€",
                "Сумма возврата": f"{r.refund_amount}€",
                "Профит": f"{r.profit()}€",
                "Процент ЗП": f"{r.salary_percent}%",
                "Партнет": partner.name,
                "Ошибочный": "Да" if r.erroneous else "Нет",
            }
        )

    file_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".xlsx"
    output_file = settings.PROJECT_DIR / "excel" / file_name
    df = pd.DataFrame(data=data)
    df.to_excel(output_file, index=False)
    return output_file
