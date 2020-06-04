# 0018010000010000000000000265310272750000010001
from utils import get_current_seconds, send_udp_message
from answer_entity import Answer


def divide_data(data):
    #делим данные на два куска - header и оставшиеся секции
    return data[:24], data[24:]


def find_part_name(name, data, index):
    for counter in range(0, int(data[index:index + 2], 16) * 2, 2):
        part_name = chr(int(data[index + counter + 2:index + counter + 4], 16))
        name += part_name
    return name + "."


def check_length(data, current_index):
    if int(data[current_index:current_index + 2], 16) == 0:
        return False
    return True


def find_part_name_marks(name, chunks, data):
    marks = int(str(bin(chunks))[4:], 2) * 2
    part_name, offset = extract_name(data, marks)
    if name == "":
        name += part_name
    else:
        name += '.' + part_name
    return name, offset


def extract_name(data, start=24):
    name = ''
    offset = 0

    while True:
        current_index = start + offset
        chunks = data[current_index:current_index + 4]
        chunks_to_int = int(chunks, 16)
        #если ссылка,то ищем по меткам
        if chunks_to_int >= 49152:
            name, offset = find_part_name_marks(name, chunks_to_int, data)
            break
        if not check_length(data, current_index):
            break
        #если это не ссылка,то собираем имя
        name = find_part_name(name, data, current_index)
        offset += int(data[current_index:current_index + 2], 16) * 2 + 2
    return name[:len(name) - 1], offset


def parse_request(data, cache):
    header, before_header = divide_data(data)
    name = extract_name(data)[0]
    type_mes = before_header[-8: -4]
    #проверяем наличие такой записи в кэше
    if (name, type_mes) in cache.keys():
        records = []
        for item in cache[(name, type_mes)]:
            format_answer = item.create_response()
            #проверяем актуальность записи
            if item.ttl > get_current_seconds():
                records.append(format_answer)
        count = len(records)
        #если нашлось необходимое в кэше,возвращаем
        if count != 0:
            print(f'Record: {name}, {type_mes} - return from cache')
            return header[:4] + "8180" + header[8:12] + hex(count)[2:].rjust(4, '0') + header[16:] + before_header + ''.join(records)
    print(f'Record: {name}, {type_mes} not find in cache')
    return None


def process_request(data, cache):
    if data is None:
        return None
    rq = parse_request(data, cache)
    #если в кэше не нашли,просим у сервера е1
    if rq is None:
        print(f'Return from server')
        response = send_udp_message(data, "195.19.71.253", 53)
        if response is None:
            return None
        parse_response(response, cache)
        return response
    return rq


def parse_count_record(header):
    return [int(header[12:16], 16), int(header[16:20], 16), int(header[20:24], 16)]


def parse_record(count, data, section, offset):
    result = []
    for i in range(count):
        #собираем записи
        chunks = int(data[offset: offset + 4], 16)
        name = find_part_name_marks("", chunks, data)[0]
        type_mes = section[4:8]
        ttl = section[12:20]
        data_length = int(section[20:24], 16) * 2
        record_data = section[24:24 + data_length]
        result.append((Answer(type_mes, ttl, record_data), name))
    return result


def parse_response(data, cache):
    header, body = divide_data(data)
    name, offset = extract_name(data)
    type_mes = body[offset - 8: offset - 4]
    list_count_records = parse_count_record(header)
    offset = 32 + len(name) * 2
    section = data[24 + offset + 8:]

    current_offset = offset
    current_section = section

    for item in list_count_records:
        #разбираем все дополнительные записи
        rec_with_name = parse_record(item, data, current_section, current_offset)
        current_section = current_section[24 + int(current_section[20:24], 16) * 2:]
        #если в кэше нет, добавляем
        for rec, rec_name in rec_with_name:
            if (rec_name, rec.type) not in cache.keys:
                cache[(rec_name, type_mes)] = [rec_with_name]
