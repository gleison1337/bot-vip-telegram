import uuid
import aiohttp
from config import WOOVI_APP_ID

API_URL = "https://api.woovi.com/api/v1/charge"

async def criar_cobranca_pix(valor_centavos: int, descricao: str):
    correlation_id = str(uuid.uuid4())
    headers = {
        "Authorization": WOOVI_APP_ID,
        "Content-Type": "application/json"
    }
    payload = {
        "correlationID": correlation_id,
        "value": valor_centavos,
        "comment": descricao
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers) as response:
            if response.status in (200, 201):
                data = await response.json()
                charge = data.get("charge", {})
                return {
                    "correlation_id": correlation_id,
                    "charge_id": charge.get("id"),
                    "brcode": charge.get("brCode"), # Código Copia e Cola
                    "qr_code_image": charge.get("qrCodeImage") # URL da imagem do QR Code
                }
            return None

async def consultar_status_pix(correlation_id: str):
    headers = {
        "Authorization": WOOVI_APP_ID,
        "Content-Type": "application/json"
    }
    url = f"{API_URL}/{correlation_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                charge = data.get("charge", {})
                return charge.get("status") # Retorna "COMPLETED", "ACTIVE", etc.
            return None