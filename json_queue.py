import asyncio
import aioserial
import json
import serial
import time
import logging
import configparser
from datetime import datetime
from random import randint


def setup_logger(name, log_file, my_format, level=logging.INFO):
    formatter = logging.Formatter(my_format)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)

    return log

async def sleep_async_rand():
    await asyncio.sleep(randint(4,8))


async def write_json_to_esp32(data_dict):
    data = json.dumps(data_dict)
    await aio_instance.write_async(data.encode())


def create_dict(id, type, seq=0, lat=5.02, log=-9.02, high=10.3, data="0"):
    return {"id": id, "type": type, "seq": seq, "lat": lat, "log": log, "high": high, "DATA": data}


async def send_drone1_json():
    seq = 0
    location_index = 0
    locations = [
        [-22.944825, -43.159063],
        [-22.947512, -43.154300],
        [-22.950713, -43.150309],
        [-22.954705, -43.157690],
        [-22.952768, -43.167088],
        [-22.946524, -43.164599]
    ]
    while True:
        lat = locations[location_index][0]
        log = locations[location_index][1]
        data_dict = create_dict(5, 35, seq=seq, lat=lat, log=log)
        await write_json_to_esp32(data_dict)
        print("Drone 1 json enviado.")
        seq += 1
        location_index += 1
        if seq >= 255:
            seq = 0
        if location_index >= len(locations):
            location_index = 0
        await sleep_async_rand()


async def send_drone2_json():
    seq = 0
    location_index = 0
    locations=[
        [-22.955258, -43.167389],
        [-22.952413, -43.165758],
        [-22.949962, -43.160394],
        [-22.947196, -43.159192],
        [-22.944311, -43.157304],
        [-22.947162, -43.1643186]
    ]
    while True:
        lat = locations[location_index][0]
        log = locations[location_index][1]
        data_dict = create_dict(6, 35, seq=seq, lat=lat, log=log)
        await write_json_to_esp32(data_dict)
        print("Drone 2 json enviado.")
        seq += 1
        location_index+=1
        if seq >= 255:
            seq = 0
        if location_index >= len(locations):
            location_index = 0
        await sleep_async_rand()



async def read_json(queue):
    while True:
        raw_data: bytes = await aio_instance.readline_async()
        decoded_line = raw_data.decode('ascii')
        try:
            json_line = json.loads(decoded_line)
            await queue.put(json_line)
        except ValueError:
            logger_exc.exception('')


async def consume(queue):
    while True:
        json_consumed = await queue.get()
        queue.task_done()
        print(f'Consumed: {json_consumed}')
        json_type = json_consumed['type']
        #Forward 1
        if json_type == 24:
            print("Forward-1")
            data_dict = create_dict(4, 25)
            await write_json_to_esp32(data_dict)
        #Forward 2
        elif json_type == 26: 
            print("Forward 2")
            data_dict = create_dict(4, 27)
            await write_json_to_esp32(data_dict)
        #Iniciar voo
        elif json_type == 28:
            print("Voo iniciado")
            data_dict = create_dict(4, 29)
            await write_json_to_esp32(data_dict)
        #Abortar voo
        elif json_type == 30:
            print("Voo abortado")
            data_dict = create_dict(4, 31)
            await write_json_to_esp32(data_dict)
        else:
            print(f'JSON unknown: {json_consumed}')
        logger_info.info(json_consumed)


async def handle_disconnection_exception(queue):
    await queue.join()
    for task in tasks:
        task.cancel()


def connect():
    config = configparser.ConfigParser()
    config.read('serial_config.ini')
    try:
        global aio_instance
        port = config['serial_esp']['port']
        baudrate = int(config['serial_esp']['baudrate'])
        aio_instance = aioserial.AioSerial(port=port, baudrate=baudrate)
        aio_instance.flush()
        return True
    except serial.serialutil.SerialException:
        logger_exc.exception('')
        return False


def keep_trying_connection():
    global is_connected
    is_connected = False
    while not is_connected:
        print("Tentando conexão com a serial...")
        is_connected = connect()
        time.sleep(3)


async def main():
    global is_connected
    global tasks

    is_connected = connect()
    while True:
        if is_connected:
            try:
                queue = asyncio.Queue()
                reader = asyncio.create_task(read_json(queue))
                consumer = asyncio.create_task(consume(queue))
                writer_drone1 = asyncio.create_task(send_drone1_json())
                writer_drone2 = asyncio.create_task(send_drone2_json())
                tasks.extend([reader, consumer, writer_drone1, writer_drone2])
                await asyncio.gather(reader)
                await handle_disconnection_exception(queue)
                is_connected = False
            except Exception:
                logger_exc.exception('')
                await handle_disconnection_exception(queue)
                keep_trying_connection()
        else:
            time.sleep(3)
            keep_trying_connection()

time_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
log_file_name_exc = f'./LOGS/exceptions-{time_now}.log'
logger_exc = setup_logger('log_exception', log_file_name_exc, '%(lineno)d: %(asctime)s %(message)s', level=logging.ERROR)

log_file_name_info = f'./LOGS/infos-{time_now}.log'
logger_info = setup_logger('log_info', log_file_name_info, '%(asctime)s %(message)s', level=logging.INFO)

tasks = []
aio_instance = None
is_connected = False

if __name__ == '__main__':
    asyncio.run(main())
