import binascii
import socket
import time
import pickle


def get_current_seconds():
    #актуальное время в секундах,для удобства проверки ttl записей
    seconds = round(time.time())
    return int(seconds)


def save_cache(cache):
    #делаем бэкап кэша в файл
    with open('cache', 'wb') as f:
        pickle.dump(cache, f)


def reload_cache():
    #попытка восстановить данные из бэкапа,если он есть
    try:
        with open('cache', 'rb+') as f:
            cache = pickle.load(f)
            print('load from cache')
            return cache
    except FileNotFoundError:
        return {}


def clear_cache(last_check_cache, server_cache):
    #чистим кэш от записей,чей ttl истек
    current_time = get_current_seconds()
    if current_time - last_check_cache >= 120:
        for _, value in server_cache.items():
            for item in value:
                if item.ttl <= current_time:
                    del item

        for key in server_cache.keys():
            if server_cache[key] is None or server_cache[key] == []:
                server_cache.pop(key)
    return get_current_seconds()


def send_udp_message(msg, address, port):
    #общение с сервером по протоколу udp
    msg = msg.replace(" ", "").replace("\n", "")
    server_address = (address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    try:
        sock.sendto(binascii.unhexlify(msg), server_address)
        response, _ = sock.recvfrom(4096)
    except Exception:
        return None
    finally:
        sock.close()
    if response is None:
        return None
    return binascii.hexlify(response).decode("utf-8")
