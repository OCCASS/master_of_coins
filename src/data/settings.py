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
