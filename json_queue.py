import asyncio
import random
import aioserial
import json
import serial
import time
import logging
from datetime import datetime


def setup_logger(name, log_file, my_format, level=logging.INFO):
    formatter = logging.Formatter(my_format)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(level)
    log.addHandler(handler)

    return log


async def rnd_sleep():
    await asyncio.sleep(random.randint(1, 3))


async def write_json_to_esp32():
    seq = 0
    while True:
        seq += 1
        data_dict = {"id": "1", "type": 1, "count": seq, "lat": 5.02, "lng": -9.02, "high": 10.3}
        data = json.dumps(data_dict)
        await aio_instance.write_async(data.encode())
        await rnd_sleep()


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
        logger_info.info(json_consumed)


async def handle_disconnection_exception(queue):
    await queue.join()
    for task in tasks:
        task.cancel()


def connect():
    try:
        global aio_instance
        aio_instance = aioserial.AioSerial(port='COM6', baudrate=115200)
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
                #writer = asyncio.create_task(write_json_to_esp32())
                tasks.extend([reader, consumer])#, writer])
                await asyncio.gather(reader)#, writer)
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