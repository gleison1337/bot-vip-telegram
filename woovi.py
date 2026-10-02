import uuid
import aiohttp
from config import WOOVI_APP_ID

API_URL = "https://api.woovi.com/api/v1/charge"

async def criar_cobranca_pix(valor_centavos: int, descricao: str):
    correlation_id = str(uuid.uuid4())
    
    app_id_limpo = WOOVI_APP_ID.strip() if WOOVI_APP_ID else ""
    
    headers = {
        "Authorization": app_id_limpo,
        "Content-Type": "application/json"
    }
    
    payload = {
        "correlationID": correlation_id,
        "value": valor_centavos,
        "comment": descricao
    }

    print(f"Enviando requisição para Woovi com AppID: {app_id_limpo[:5]}...")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers) as response:
            resposta_texto = await response.text()
            print(f"Status HTTP Woovi: {response.status}")
            print(f"Resposta Woovi: {resposta_texto}")

            if response.status in (200, 201):
                data = await response.json()
                charge = data.get("charge", {})
                return {
                    "correlation_id": correlation_id,
                    "charge_id": charge.get("id"),
                    "brcode": charge.get("brCode"),
                    "qr_code_image": charge.get("qrCodeImage")
                }
            return None