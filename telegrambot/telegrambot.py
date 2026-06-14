import os
import logging
import ssl
import certifi
import aiomqtt

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, filters, MessageHandler

# ver logs
logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# token del bot
TOKEN=os.environ["TB_TOKEN"]
MQTT_BROKER = os.environ.get("MQTT_USR", "mosquitto") 
MQTT_PORT = 8883 
MQTT_USER = os.environ.get("MQTT_USR", None)
MQTT_PASS = os.environ.get("MQTT_PASS", None)

# La mac de la raspeberry pi pico 2W
MAC_PICO = os.environ.get("DEVICE_MAC", "AA:BB:CC:DD:EE:FF")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "*Panel de Control del Termostato* \n\n"
        "Comandos disponibles:\n"
        "<code>/setpoint [número]</code> - Fija la temperatura objetivo\n"
        "<code>/periodo [segundos]</code> - Tiempo entre lecturas\n"
        "<code>/modo [auto|manual]</code> - Alterna entre Auto/Manual (Menú)\n"
        "<code>/rele [on|off]</code> - Control manual del relé (Menú)\n"
        "<code>/destello</code> - Identificar dispositivo"
    )
    await update.message.reply_text(
        texto, 
        parse_mode='HTML'
    )

async def publicar_mqtt(topico_final: str, mensaje: str):
    topico = f"{MAC_PICO}/{topico_final}"
    
    # Configuración TLS (seguridad)
    contexto_ssl = ssl.create_default_context(cafile=certifi.where())
    contexto_ssl.check_hostname = False
    contexto_ssl.verify_mode = ssl.CERT_NONE

    try:
        async with aiomqtt.Client(
            hostname=MQTT_BROKER,
            port=MQTT_PORT,
            username=MQTT_USER,
            password=MQTT_PASS,
            tls_context=contexto_ssl
        ) as cliente:
            await cliente.publish(topico, payload=mensaje, qos=1)
            logging.info(f"MQTT -> Publicado en {topico}: {mensaje}")
            return True
    except Exception as e:
        logging.error(f"Error MQTT: {e}")
        return False

# Establece temperatura objetivo -> /setpoint [numero]
async def setpoint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ADVERTENCIA - uso esperado: `/setpoint <numero>`.  Ejemplo: /setpoint 20")
        return
    
    valor=context.args[0]
    try:
        float(valor) # Validamos que sea un número
        exito = await publicar_mqtt("setpoint", valor)
        if exito:
            await update.message.reply_text(f"Setpoint de temperatura actualizado a *{valor}°C*", parse_mode='Markdown')
        else:
            await update.message.reply_text("¡¡¡¡ Error al enviar al broker !!!!")
    except ValueError:
        await update.message.reply_text("Por favor, ingresá un número válido (ej: 24 o 25.5).")

# Establece periodo de lectura del sensor (velocidad de lectura) -> /periodo [segundos]
async def periodo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("DVERTENCIA - uso esperado: `/periodo <numero>`", parse_mode='Markdown')
        return
    
    valor = context.args[0]
    if valor.isdigit(): # Validamos que sea numerito entero positivo
        exito = await publicar_mqtt("periodo", valor)
        if exito:
            await update.message.reply_text(f"Periodo de lectura fijado en *{valor}s*", parse_mode='Markdown')
    else:
        await update.message.reply_text("Por favor, ingresá un número entero sin decimales.")


# Cambia el modo del termostado -> /modo [auto | manual]
async def modo_termostado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_actual = update.effective_message

    if not context.args:
        await mensaje_actual.reply_text("Uso: /modo <auto|manual>")
        return
    
    modo = context.args[0].lower()

    if modo not in ["auto", "manual"]:
        await mensaje_actual.reply_text("Modo inválido. Usa 'auto' o 'manual'.")
        return
    
    exito = await publicar_mqtt("modo", modo)
    if exito:
        await mensaje_actual.reply_text(f"Modo: {modo.upper()}")
    else:
        await mensaje_actual.reply_text("Error de conexión MQTT.")

# Establece moodo de rele, prendido o apagado -> /rele [on | off]
async def rele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_actual = update.effective_message

    if not context.args:
        await mensaje_actual.reply_text("Uso esperado: /rele [ on | off ]")
        return
    
    estado = context.args[0].upper()
    
    if estado not in ["ON", "OFF"]:
        await mensaje_actual.reply_text("Estado inválido. Usa 'on' o 'off'.")
        return
   
    payload_rele = "1" if estado == "ON" else "0"

    exito = await publicar_mqtt("rele", payload_rele)
    if exito:
        await mensaje_actual.reply_text(f"Relé: {estado}")
    else:
        await mensaje_actual.reply_text("Error de conexión MQTT.")

async def destello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    exito = await publicar_mqtt("destello", "1")
    if exito:
        await update.message.reply_text("Orden de destello enviada a la Raspberry Pico.")
        
async def medicion(update: Update, context):
    logging.info(update.message.text)
    sql = f"SELECT timestamp, {update.message.text} FROM mediciones ORDER BY timestamp DESC LIMIT 1"
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        r = await cur.fetchone()
        if update.message.text == 'temperatura':
            unidad = 'ºC'
        else:
            unidad = '%'
        await context.bot.send_message(update.message.chat.id,
                                    text="La última {} es de {} {},\nregistrada a las {:%H:%M:%S %d/%m/%Y}"
                                    .format(update.message.text, str(r[1]).replace('.',','), unidad, r[0]))
        logging.info("La última {} es de {} {}, medida a las {:%H:%M:%S %d/%m/%Y}".format(update.message.text, r[1], unidad, r[0]))
    conn.close()
    
async def graficos(update: Update, context):
    logging.info(update.message.text)
    sql = f"""SELECT timestamp, {update.message.text.split()[1]}
            FROM (
                SELECT timestamp, {update.message.text.split()[1]},
                    ROW_NUMBER() OVER (ORDER BY id) AS rn
                FROM mediciones
                WHERE timestamp >= NOW() - INTERVAL 1 DAY
                AND sensor_id LIKE 'sensor_1'
            ) AS t
            WHERE rn % 2 = 0
            ORDER BY timestamp;"""
    conn = await aiomysql.connect(host=os.environ["MARIADB_SERVER"], port=3306,
                                    user=os.environ["MARIADB_USER"],
                                    password=os.environ["MARIADB_USER_PASS"],
                                    db=os.environ["MARIADB_DB"])
    async with conn.cursor() as cur:
        await cur.execute(sql)
        filas = await cur.fetchall()

        fig, ax = plt.subplots(figsize=(7, 4))
        fecha,var=zip(*filas)
        ax.plot(fecha,var)
        ax.grid(True, which='both')
        ax.set_title(update.message.text, fontsize=14, verticalalignment='bottom')
        ax.set_xlabel('fecha')
        ax.set_ylabel('unidad')

        buffer = BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buffer)
        buffer.close()
    conn.close()
    
async def acercade(update: Update, context):
    await context.bot.send_message(update.message.chat.id, text="Este bot fue creado para el curso de IoT FIO")
    


def main():
    
    application = Application.builder().token(TOKEN).build()
    
    # funciones:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setpoint", setpoint))
    application.add_handler(CommandHandler("periodo", periodo))
    application.add_handler(CommandHandler("destello", destello))
    application.add_handler(CommandHandler('acercade', acercade))
    application.add_handler(MessageHandler(filters.Regex("^(temperatura|humedad)$"), medicion))
    application.add_handler(MessageHandler(filters.Regex("^(gráfico temperatura|gráfico humedad)$"), graficos))
    application.add_handler(CommandHandler("modo", modo_termostado))
    application.add_handler(CommandHandler("rele", rele))
    
    application.run_polling()

if __name__ == '__main__':
    main()