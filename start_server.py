import binascii
from parser_data import process_request
from utils import save_cache, reload_cache, get_current_seconds, clear_cache
import socket


def run_server(udp_sock, server_cache):
    #обработка данных,приходящих и уходящих с сервера
    data, addr = udp_sock.recvfrom(4096)
    b_data = binascii.hexlify(data).decode("utf-8")
    rp = process_request(b_data, server_cache)
    if rp is not None:
        udp_sock.sendto(binascii.unhexlify(rp), addr)


def main():
    last_check_cache = get_current_seconds()
    # смотрим, есть ли у нас данные для восстановления кэша при запуска
    server_cache = reload_cache()
    print(f"Cache: {server_cache}")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', 53))
    print('Server start working on 53 port')

    while True:
        #вечный цикл работы сервера,обработка данных и проверка записей кэша на актуальность
        try:
            run_server(sock, server_cache)
            last_check_cache = clear_cache(last_check_cache, server_cache)
        except KeyboardInterrupt:
            #работа сервера прекращена,сохраняем кэш для последующего перезапуска
            print('server crashed')
            save_cache(server_cache)
            exit(1)


if __name__ == '__main__':
    main()
