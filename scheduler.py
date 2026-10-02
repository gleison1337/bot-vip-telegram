from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import database
from config import CANAL_VIP_ID

async def checar_vencimentos(bot: Bot):
    expirados = await database.get_assinaturas_expiradas()
    for row in expirados:
        user_id = row[0]
        try:
            # Bane e desbane para apenas expulsar o membro do canal privado
            await bot.ban_chat_member(chat_id=CANAL_VIP_ID, user_id=user_id)
            await bot.unban_chat_member(chat_id=CANAL_VIP_ID, user_id=user_id)
            await database.desativar_assinatura(user_id)
            await bot.send_message(
                chat_id=user_id,
                text="⚠️ Sua assinatura do VIP expirou. Envie /start para renovar e recuperar seu acesso."
            )
        except Exception:
            pass

def iniciar_agendador(bot: Bot):
    scheduler = AsyncIOScheduler()
    # Roda a verificação a cada 1 hora
    scheduler.add_job(checar_vencimentos, "interval", hours=1, args=[bot])
    scheduler.start()