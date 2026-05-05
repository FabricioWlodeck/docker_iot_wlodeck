import asyncio, ssl, certifi, logging, os
import aiomqtt

# lo que recive por consola al ejecutar docker seria algo asi:
# ... docker run -e SERVIDOR="fiounam.duckdns.org" -e TOPICO_1="/temperatura" -e TOPICO_2="/humedad" -e TOPICO_3="/contador" --rm --name cliente_mqtt clientemqtt 

logging.basicConfig(
    format='%(asctime)s - [%(taskName)s] - %(levelname)s: %(message)s', 
    level=logging.INFO, 
    datefmt='%d/%m/%Y %H:%M:%S %z'
)

# corrutinas para los distintos topicos
async def corrutina_topico_1(message):
    logging.info("Topico 1 - " + str(message.topic) + ": " + message.payload.decode("utf-8")) 
sss
async def corrutina_topico_2(message):
    logging.info("Topico 2 - " + str(message.topic) + ": " + message.payload.decode("utf-8")) 

async def corrutina_topico_3(message):
    logging.info("Topico 3 - " + str(message.topic) + ": " + message.payload.decode("utf-8")) 

# contador cada 5 seg
async def contador(client, topico):
    contador = 0
    while True:
        try:
            contador += 1
            await client.publish(topico, payload=str(contador))
            await asyncio.sleep(5)
        except Exception:
            logging.exception(f"\nError en el contador")
            break
    

async def main():
    # recivo los datos por variable de entorno
    broker_direccion = os.environ.get('SERVIDOR')
    topico_1 = os.environ.get('TOPICO_1', 'por_defecto/temperatura')
    topico_2 = os.environ.get('TOPICO_2', 'por_defecto/humedad')
    topico_contador = os.environ.get('TOPICO_3', 'por_defecto/contador')
    
    
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True
    tls_context.load_default_certs()

    async with aiomqtt.Client(
        broker_direccion,
        port=8883,
        tls_context=tls_context,
    ) as client:
        await client.subscribe(topico_1)
        await client.subscribe(topico_2)
        
        # inicio contador y lo dejo corriendo de fondo
        asyncio.create_task(contador(client, topico_contador)) 
        
        async for message in client.messages:
            if message.topic == topico_1:
                asyncio.create_task(corrutina_topico_1(message))
                
            elif message.topic == topico_2:
                asyncio.create_task(corrutina_topico_2(message))
                
            else:
                asyncio.create_task(corrutina_topico_3(message))
                



if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Aplicacion detenida por [Ctrl+C]")