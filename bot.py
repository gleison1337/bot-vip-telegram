import os
import asyncio
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
    # Texto de apresentação no mesmo estilo do modelo[cite: 1]
    texto = (
        "🇧🇷🔥 **MEU VIP INTIMIDADE +18** 🔥\n\n"
        "🎬 Conteúdos sem censura atualizados toda semana.\n"
        "❤️ Vídeos e fotos transando, mamando e gozando gostoso.\n"
        "🎁 Brinquedos especiais e novidades diárias.\n"
        "💬 Chat quente e safado com os assinantes.\n\n"
        "👇 **ESCOLHA SEU PLANO E ACESSE AGORA:**"
    )

    caminho_video = "media/preview.mp4"

    # Se houver o arquivo preview.mp4 na pasta media, envia como vídeo em looping/preview
    if os.path.exists(caminho_video):
        video = FSInputFile(caminho_video)
        await message.answer_video(
            video=video,
            caption=texto,
            parse_mode="Markdown",
            reply_markup=teclado_planos()
        )
    else:
        # Fallback caso ainda não tenha colocado o vídeo na pasta
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

    # Registra no banco de dados
    await database.salvar_cobranca(
        correlation_id=pix_data["correlation_id"],
        charge_id=pix_data["charge_id"],
        user_id=callback.from_user.id,
        plano_key=plano_key
    )

    teclado_verificacao = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Já Paguei / Verificar Acesso", callback_data=f"check_{pix_data['correlation_id']}")]
    ])

    mensagem_pix = (
        f"💳 **Fatura Gerada - {plano['nome']}**\n\n"
        f"💰 **Valor:** R$ {plano['preco_reais']:.2f}\n\n"
        f"Copie a chave Pix abaixo e pague no app do seu banco:\n\n"
        f"`{pix_data['brcode']}`\n\n"
        "Após o pagamento, clique no botão abaixo para liberar seu link exclusivo:"
    )

    await callback.message.answer(
        mensagem_pix,
        parse_mode="Markdown",
        reply_markup=teclado_verificacao
    )

@dp.callback_query(F.data.startswith("check_"))
async def verificar_pagamento(callback: CallbackQuery):
    correlation_id = callback.data.split("_")[1]
    status = await woovi.consultar_status_pix(correlation_id)

    if status == "COMPLETED":
        dados = await database.get_cobranca(correlation_id)
        if not dados:
            await callback.answer("Cobrança não encontrada.", show_alert=True)
            return

        plano_key = dados[2]
        plano = PLANOS[plano_key]
        user = callback.from_user

        # Ativa a assinatura no banco de dados
        await database.ativar_ou_renovar_assinatura(
            user_id=user.id,
            username=user.username or "",
            dias=plano["dias"]
        )

        # Gera link exclusivo para 1 pessoa (não reutilizável)
        link = await bot.create_chat_invite_link(
            chat_id=CANAL_VIP_ID,
            member_limit=1
        )

        await callback.message.edit_text(
            f"🎉 **Pagamento Confirmado com Sucesso!**\n\n"
            f"Seu acesso de **{plano['dias']} dias** foi liberado.\n"
            f"Entre no canal pelo link exclusivo abaixo:\n\n"
            f"{link.invite_link}\n\n"
            "*(Este link expira após o seu primeiro acesso)*",
            disable_web_page_preview=True
        )
    else:
        await callback.answer(
            "⏳ O pagamento ainda não foi identificado. Aguarde alguns segundos após pagar no banco e clique novamente.",
            show_alert=True
        )

async def main():
    await database.init_db()
    scheduler.iniciar_agendador(bot)
    print("Bot VIP inicializado com sucesso!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())