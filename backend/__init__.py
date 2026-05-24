from backend.core.database import load_all_models

# Прогреваем реестр моделей при любом обращении к пакету backend
load_all_models()
