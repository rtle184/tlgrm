from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import qrcode
import io
import crcmod
from unidecode import unidecode
from datetime import datetime

TOKEN = "8227369400:AAE73Hb-AEZC-UZxMhJajv7xaQScwCK9U1s"

# Sua chave PIX (e-mail, CPF, CNPJ ou aleatória)
CHAVE_PIX = "e96bc856-affa-4c0c-ab59-5dfcc732ef34"
NOME_RECEBEDOR = "GUSTAVO E R R OLIVEIRA"
CIDADE_RECEBEDOR = "BALNEARIO CAMBORIU"

# Limites PIX
MAX_LEN_NOME = 25
MAX_LEN_CIDADE = 15

# Ajusta nome e cidade para o tamanho máximo permitido e remove acentos
NOME_RECEBEDOR = unidecode(NOME_RECEBEDOR).upper()[:MAX_LEN_NOME]
CIDADE_RECEBEDOR = unidecode(CIDADE_RECEBEDOR).upper()[:MAX_LEN_CIDADE]

# Função para gerar CRC16 exigido pelo BACEN
def crc16(payload: str):
    crc16_func = crcmod.predefined.mkPredefinedCrcFun('crc-ccitt-false')
    checksum = crc16_func(payload.encode('utf-8'))
    return format(checksum, '04X')

# Função para gerar o PIX copia e cola + QRCode
def gerar_pix(valor: float, descricao: str):
    valor_str = f"{valor:.2f}"
    
    payload = (
        "000201"
        "26" + f"{len('0014BR.GOV.BCB.PIX01'+str(len(CHAVE_PIX)).zfill(2)+CHAVE_PIX):02}" +
        "0014BR.GOV.BCB.PIX" +
        "01" + f"{len(CHAVE_PIX):02}" + CHAVE_PIX +
        "52040000"
        "5303986"
        "54" + f"{len(valor_str):02}" + valor_str +
        "5802BR" +
        "59" + f"{len(NOME_RECEBEDOR):02}" + NOME_RECEBEDOR +
        "60" + f"{len(CIDADE_RECEBEDOR):02}" + CIDADE_RECEBEDOR +
        "62" + f"{len('0503***'):02}" + "0503***" +
        "6304"
    )
    payload += crc16(payload)
    
    img = qrcode.make(payload)
    bio = io.BytesIO()
    bio.name = "pix.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return payload, bio

# Funções auxiliares que usam message diretamente
async def previas_msg(message):
    fotos = [
        "https://vago-sc.com/tlgrm/foto1.jpg",
        "https://vago-sc.com/tlgrm/foto2.jpg",
        "https://vago-sc.com/tlgrm/foto3.jpg"
    ]
    for f in fotos:
        await message.reply_photo(f)
    
    # Depois de enviar todas as fotos, adicionar botão VIP
    keyboard = [[InlineKeyboardButton("💎 Assinar VIP", callback_data="menu_vip")]]
    await message.reply_text(
        "Quer desbloquear tudo? Assine o VIP agora:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def vip_msg(message):
    keyboard = [
        [InlineKeyboardButton("💳 Pagar R$ 7,99", callback_data="pagar_vip")]
    ]
    await message.reply_text(
        "💎 VIP disponível por apenas R$ 7,99.\nClique no botão abaixo para gerar seu PIX:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# /start - menu inicial
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📸 Ver Prévias", callback_data="menu_previas")],
        [InlineKeyboardButton("💎 Assinar VIP", callback_data="menu_vip")]
    ]
    await update.message.reply_text(
        f"Olá {update.effective_user.first_name}! Escolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# /previas
async def previas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await previas_msg(update.message)

# /vip
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await vip_msg(update.message)

# Botão pagar e menu
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "pagar_vip":
        payload, qrcode_img = gerar_pix(7.99, "VIP Telegram")
        
        # Envia QRCode
        await query.message.reply_photo(qrcode_img, caption="📸 Escaneie para pagar\nOu use o código abaixo:")

        # Envia PIX copia e cola
        await query.message.reply_text(f"```\n{payload}\n```", parse_mode="Markdown")

        # LOG no terminal
        user = query.from_user
        username = user.username or user.first_name
        user_id = user.id
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"[{now}] PIX gerado por {username} (ID: {user_id})")
        print(f"Payload: {payload}")
        print("------------------------------------")

    elif query.data == "menu_previas":
        await previas_msg(query.message)
    elif query.data == "menu_vip":
        await vip_msg(query.message)

# Monta o bot
application = ApplicationBuilder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("previas", previas))
application.add_handler(CommandHandler("vip", vip))
application.add_handler(CallbackQueryHandler(button_handler))

application.run_polling()
