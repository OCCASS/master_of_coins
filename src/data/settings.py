from pathlib import Path

from environs import Env

BASE_DIR = Path(__file__).parent.parent
PROJECT_DIR = BASE_DIR.parent
TEMPLATES_DIR = PROJECT_DIR / "templates"
ENV_FILE = PROJECT_DIR / ".env"

env = Env()
env.read_env(str(ENV_FILE.absolute()))

BOT_TOKEN = env.str("BOT_TOKEN")
POSTGRESQL_URI = env.str("POSTGRESQL_URI")

BET_20_PARTNER_ID = 1
MISHA_PARTNER_ID = 2
BET_20_SALARY_FRACTION = 0.3
CHARITY_FRACTION = 0.005  # 0.5%
DEFAULT_SALARY_FRACTION = 0.12

MIN_SALARY_PERCENT, MAX_SALARY_PERCENT = 0, 12
