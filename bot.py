import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)

from config import BOT_TOKEN, CANAL_VIP_ID, PLANOS
import database
import woovi
import scheduler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def teclado_planos():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="VIP - 1 MÊS por R$ 9,99", callback_data="buy_1m")],
        [InlineKeyboardButton(text="VIP - 3 MESES por R$ 16,99", callback_data="buy_3m")],
        [InlineKeyboardButton(text="VIP - 1 ANO por R$ 19,90", callback_data="buy_1a")],
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    texto = (
        "🇧🇷🔥 **MEU VIP INTINIDADE +18** 🔥\n\n"
        "🎬 Conteúdos sem censura atualizados toda semana.\n"
        "❤️ Vídeos e fotos transando, mamando e gozando gostoso.\n"
        "🎁 Brinquedos especiais e novidades diárias.\n"
        "💬 Chat quente e safado com os assinantes.\n\n"
        "👇 **ESCOLHA SEU PLANO E ACESSE AGORA:**"
    )

    caminho_video = "media/preview.mp4"

    if os.path.exists(caminho_video):
        video = FSInputFile(caminho_video)
        await message.answer_video(
            video=video,
            caption=texto,
            parse_mode="Markdown",
            reply_markup=teclado_planos()
        )
    else:
        await message.answer(
            text=texto,
            parse_mode="Markdown",
            reply_markup=teclado_planos()
        )

@dp.callback_query(F.data.startswith("buy_"))
async def gerar_pix(callback: CallbackQuery):
    plano_key = callback.data.split("_")[1]
    plano = PLANOS[plano_key]

    await callback.answer("Gerando Pix da Woovi...", show_alert=False)

    descricao = f"{plano['nome']} - VIP Telegram"
    pix_data = await woovi.criar_cobranca_pix(plano["preco_centavos"], descricao)

    if not pix_data:
        await callback.message.answer("❌ Erro ao gerar o Pix. Tente novamente em instantes.")
        return

    await database.salvar_cobranca(
        correlation_id=pix_data["correlation_id"],
        charge_id=pix_data["charge_id"],
        user_id=callback.from_user.id,
        plano_key=plano_key
    )

    mensagem_pix = (
        f"💳 **Fatura Gerada - {plano['nome']}**\n\n"
        f"💰 **Valor:** R$ {plano['preco_reais']:.2f}\n\n"
        f"Copie a chave Pix Copia e Cola abaixo e pague no app do seu banco:\n\n"
        f"`{pix_data['brcode']}`\n\n"
        "⚡ *Assim que o pagamento for aprovado pelo banco, seu link de acesso será enviado automaticamente aqui no chat!*"
    )

    await callback.message.answer(
        mensagem_pix,
        parse_mode="Markdown"
    )

# --- ENDPOINT DO WEBHOOK DA WOOVI ---
async def handle_woovi_webhook(request):
    try:
        data = await request.json()
        evento = data.get("event")
        
        if evento == "PixReceived" or data.get("charge", {}).get("status") == "COMPLETED":
            charge = data.get("charge", {})
            correlation_id = charge.get("correlationID")
            
            if correlation_id:
                dados_cob = await database.get_cobranca_por_correlation(correlation_id)
                if dados_cob:
                    user_id, plano_key = dados_cob
                    plano = PLANOS[plano_key]

                    await database.atualizar_status_cobranca(correlation_id, "COMPLETED")
                    await database.ativar_ou_renovar_assinatura(
                        user_id=user_id,
                        username="",
                        dias=plano["dias"]
                    )

                    link = await bot.create_chat_invite_link(
                        chat_id=CANAL_VIP_ID,
                        member_limit=1
                    )

                    await bot.send_message(
                        chat_id=user_id,
                        text=(
                            f"🎉 **Pagamento Confirmado Automaticamente!**\n\n"
                            f"Seu acesso de **{plano['dias']} dias** foi liberado com sucesso.\n"
                            f"Entre no canal pelo link exclusivo abaixo:\n\n"
                            f"{link.invite_link}\n\n"
                            "*(Este link expira após o seu primeiro acesso)*"
                        ),
                        disable_web_page_preview=True
                    )

        return web.json_response({"status": "ok"}, status=200)
    except Exception as e:
        print(f"Erro no webhook: {e}")
        return web.json_response({"status": "error"}, status=500)

async def main():
    await database.init_db()
    scheduler.iniciar_agendador(bot)

    # Configuração e inicialização imediata do servidor aiohttp na porta exigida pelo Render
    app = web.Application()
    app.router.add_post("/webhook/woovi", handle_woovi_webhook)
    
    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Servidor Webhook escutando na porta {port}")

    print("Bot VIP iniciado com sucesso!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())