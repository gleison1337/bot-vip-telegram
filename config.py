import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WOOVI_APP_ID = os.getenv("WOOVI_APP_ID")
CANAL_VIP_ID = int(os.getenv("CANAL_VIP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Tabela de planos e valores em centavos para a API da Woovi
PLANOS = {
    "1m": {
        "nome": "VIP - 1 MÊS",
        "dias": 30,
        "preco_reais": 9.99,
        "preco_centavos": 999
    },
    "3m": {
        "nome": "VIP - 3 MESES",
        "dias": 90,
        "preco_reais": 16.99,
        "preco_centavos": 1699
    },
    "1a": {
        "nome": "VIP - 1 ANO",
        "dias": 365,
        "preco_reais": 19.90,
        "preco_centavos": 1990
    }
}