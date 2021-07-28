import asyncio
import aioserial
import json
import serial
import time
import logging
import configparser
from datetime import datetime
from random import randint

TIME_DRONE_SLEEP = 1
TIME_OFF = 30


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


async def sleep_async(seconds):
    await asyncio.sleep(seconds)


async def write_json_to_esp32(data_dict):
    data = json.dumps(data_dict) + '\n'
    await aio_instance.write_async(data.encode())


def create_dict(id, type, seq=0, lat=5.02, log=-9.02, high=10.3, data="0", device_type='uav'):
    return {"id": id, "type": type, "seq": seq, "lat": lat, "log": log, "high": high, "DATA": data, "device": device_type}


async def send_drone_json(id):
  global path
  locations = path.copy()
  seq = 0
  location_index = 0
  await sleep_async((id-1)*TIME_OFF)
  while True:
    lat = locations[location_index][0]
    log = locations[location_index][1]
    data_dict = create_dict(id, 102, seq=seq, lat=lat, log=log)
    await write_json_to_esp32(data_dict)

    seq += 1
    location_index+=1
    if seq >= 255:
      seq = 0
    if location_index >= len(locations):
      location_index = 0
      locations.reverse()
    await sleep_async(TIME_DRONE_SLEEP)


async def send_drone1_json():
  await send_drone_json(1)

async def send_drone2_json():
  await send_drone_json(2)


async def read_json(queue):
    while True:
        raw_data: bytes = await aio_instance.readline_async()
        decoded_line = raw_data.decode('ascii')
        print(decoded_line)
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
                await asyncio.gather(*tasks)
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

path=[
    #[-15.840068,-47.926633],
    [-15.83852760,-47.92653140],
    [-15.83851990,-47.92661460],
    [-15.83852250,-47.92670580],
    [-15.83851730,-47.92681840],
    [-15.83853790,-47.92694180],
    [-15.83853020,-47.92704110],
    [-15.83853280,-47.92711350],
    [-15.83854050,-47.92720200],
    [-15.83853020,-47.92729850],
    [-15.83854050,-47.92738710],
    [-15.83853540,-47.92749170],
    [-15.83854310,-47.92758550],
    [-15.83854050,-47.92767410],
    [-15.83855860,-47.92783500],
    [-15.83857150,-47.92792890],
    [-15.83856380,-47.92801740],
    [-15.83857410,-47.92810050],
    [-15.83857150,-47.92817560],
    [-15.83857150,-47.92824540],
    [-15.83857410,-47.92833920],
    [-15.83857410,-47.92846260],
    [-15.83857670,-47.92854310],
    [-15.83857670,-47.92863160],
    [-15.83857920,-47.92871740],
    [-15.83858700,-47.92880060],
    [-15.83859730,-47.92889450],
    [-15.83859470,-47.92896690],
    [-15.83861540,-47.92908760],
    [-15.83867470,-47.92905270],
    [-15.83875990,-47.92905000],
    [-15.83885790,-47.92907420],
    [-15.83893270,-47.92908220],
    [-15.83903850,-47.92910100],
    [-15.83911600,-47.92909290],
    [-15.83918560,-47.92910900],
    [-15.83930950,-47.92912240],
    [-15.83942300,-47.92913850],
    [-15.83954170,-47.92914930],
    [-15.83963720,-47.92915730],
    [-15.83970430,-47.92916800],
    [-15.83978430,-47.92917340],
    [-15.83985390,-47.92918150],
    [-15.83995720,-47.92919490],
    [-15.84003970,-47.92920290],
    [-15.84012230,-47.92921630],
    [-15.84020740,-47.92922440],
    [-15.84027970,-47.92921630],
    [-15.84034680,-47.92923780],
    [-15.84041390,-47.92924580],
    [-15.84048610,-47.92925390],
    [-15.84058930,-47.92927000],
    [-15.84068740,-47.92928870],
    [-15.84080610,-47.92929950],
    [-15.84089640,-47.92929950],
    [-15.84101770,-47.92932090],
    [-15.84112350,-47.92932900],
    [-15.84123180,-47.92933970],
    [-15.84135050,-47.92935850],
    [-15.84145630,-47.92937730],
    [-15.84155440,-47.92939070],
    [-15.84164990,-47.92938800],
    [-15.84173500,-47.92940410],
    [-15.84185110,-47.92940940],
    [-15.84194920,-47.92943090],
    [-15.84205760,-47.92944430],
    [-15.84214270,-47.92945500],
    [-15.84224080,-47.92945770],
    [-15.84231300,-47.92947650],
    [-15.84248850,-47.92948720],
    [-15.84246780,-47.92926730],
    [-15.84246780,-47.92913850],
    [-15.84248330,-47.92896420],
    [-15.84248850,-47.92886230],
    [-15.84250390,-47.92870130],
    [-15.84250650,-47.92858060],
    [-15.84252460,-47.92844380],
    [-15.84251430,-47.92833660],
    [-15.84252200,-47.92823200],
    [-15.84251940,-47.92814880],
    [-15.84253490,-47.92808440],
    [-15.84254780,-47.92794500],
    [-15.84253490,-47.92782430],
    [-15.84256850,-47.92763920],
    [-15.84257360,-47.92746480],
    [-15.84258140,-47.92734680],
    [-15.84258910,-47.92721000],
    [-15.84258910,-47.92709200],
    [-15.84259680,-47.92699810],
    [-15.84260200,-47.92689620],
    [-15.84260720,-47.92677020],
    [-15.84261490,-47.92668700],
    [-15.84261490,-47.92659850],
    [-15.84264330,-47.92645630],
    [-15.84257880,-47.92635170],
    [-15.84253750,-47.92623910],
    [-15.84248330,-47.92615320],
    [-15.84243430,-47.92604860],
    [-15.84240590,-47.92591720],
    [-15.84235950,-47.92580990],
    [-15.84230780,-47.92569730],
    [-15.84226400,-47.92558460],
    [-15.84223040,-47.92550410],
    [-15.84218400,-47.92539950],
    [-15.84215300,-47.92529490],
    [-15.84207050,-47.92513670],
    [-15.84204720,-47.92499990],
    [-15.84196980,-47.92484700],
    [-15.84190530,-47.92470220],
    [-15.84186660,-47.92459760],
    [-15.84183310,-47.92450370],
    [-15.84177630,-47.92439910],
    [-15.84173760,-47.92425960],
    [-15.84169630,-47.92418180],
    [-15.84165760,-47.92406380],
    [-15.84162920,-47.92399410],
  ]

if __name__ == '__main__':
    asyncio.run(main())
