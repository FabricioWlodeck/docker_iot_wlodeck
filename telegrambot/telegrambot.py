import os
import logging
import ssl
import certifi
import aiomqtt

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import logging, os, asyncio, aiomysql, traceback, locale
import matplotlib.pyplot as plt
from io import BytesIO

# ver logs
logging.basicConfig(format='%(asctime)s - TelegramBot - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)


# token del bot
TOKEN=os.environ["TB_TOKEN"]
MQTT_BROKER = os.environ.get("SERVIDOR", None) 
MQTT_PORT = 8883  # Puerto Mqtts seguro con TLS o SSL
MQTT_USER = os.environ.get("MQTT_USER", None)
MQTT_PASS = os.environ.get("MQTT_PASS", None)
MAC_PICO = os.environ.get("DEVICE_MAC", "AA:BB:CC:DD:EE:FF") # La MAC de la PICO 2W



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "*Panel de Control del Termostato* \n\n"
        "Comandos disponibles:\n"
        "/setpoint <número>` - Fija la temperatura objetivo\n"
        "`/periodo <segundos>` - Tiempo entre lecturas\n"
        "`/modo` - Alterna entre Auto/Manual (Menú)\n"
        "`/rele` - Control manual del relé (Menú)\n"
        "`/destello` - Identificar dispositivo"
    )
    await update.message.reply_text(texto, parse_mode='Markdown')


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



def main():
    
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    
    
    application.run_polling()

if __name__ == '__main__':
    main()
