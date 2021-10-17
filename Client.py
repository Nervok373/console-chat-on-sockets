import asyncio
import random
import socket
import sys
import threading
import time


# шифровка сообщение
def message_encrypt(text):
    random.seed(key_noise)
    endtext = []

    for i in text:
        x = ord(i) + key_cez
        while True:
            if x > 1103:
                x -= 1103
            else:
                break

        endtext.append(chr(random.randint(32, 255)))
        endtext.append(chr(x))

    return ''.join(endtext)


# расшифровка сообщение
def message_decrypt(text):
    endtext = []
    random.seed(key_noise)
    for ii, jj in enumerate(text):
        if ii % 2 == 0:
            continue
        x = chr(random.randint(32, 1103))
        if jj != x:
            jjord = ord(jj)
            jjord -= key_cez
            while True:
                if jjord < 32:
                    jjord += 1103
                else:
                    break
            endtext.append(chr(jjord))

    return ''.join(endtext)


# получение ключей
def get_key():
    global key_cez, key_noise
    key_cez = round((int(time_run_server.split(':')[0]) * int(time_run_server.split(':')[1]) * int(
        time_run_server.split(':')[2]) * 1.37219837) /
                    (int(time_run_server.split(':')[0]) + int(time_run_server.split(':')[1]) + int(
                        time_run_server.split(':')[2])))
    x1 = int(time_run_server.split(':')[0]) ** 2 + int(time_run_server.split(':')[1]) ** 2 + int(
        time_run_server.split(':')[2]) ** 3
    key_noise = (int(time_run_server.split(':')[0]) * x1 * 724) * (int(time_run_server.split(':')[0] * 23) * x1) * (
            int(time_run_server.split(':')[0]) * x1 * 194)


# запуск чата/сервера
async def run_server(host, port, password):
    global sock, server_settings, time_run_server, key_cez, key_noise
    server_settings = {'server_password': password,
                       'anon_list': [[], []]}  # addr, name
    # ключи шифра~
    time_run_server = time.strftime("%H:%M:%S", time.localtime())
    get_key()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((str(host), int(port)))
    print('client-server starting ')
    await read_request()


# палучение сообщений отправленых на сервер
async def read_request():
    while True:
        data, addres = sock.recvfrom(1024)
        if server_settings['anon_list'][0].count(addres) == 0:
            await server_add_client(data, addres)
            continue

        if data.decode('utf-8')[:1] == '/':
            command = data.decode('utf-8')

            # проверка на команды
            if command == '/quit':
                name = server_settings["anon_list"][1][server_settings["anon_list"][0].index(addres)]
                print(f'disconnect {addres} {name}')
                server_settings["anon_list"][0].remove(addres)
                server_settings["anon_list"][1].remove(name)
                sock.sendto(message_encrypt(f'you are disconnected from the server').encode('utf-8'), addres)
                for i in server_settings['anon_list'][0]:
                    sock.sendto(message_encrypt(f' {name} disconnect!').encode('utf-8'), i)

            elif 'ban' in command:
                if server_settings["anon_list"][0].index(addres) == 0:
                    addr = server_settings["anon_list"][0][server_settings["anon_list"][1].index(command.split(' ')[1])]
                    print(f'ban {addr} {command.split(" ")[1]}')
                    server_settings["anon_list"][0].remove(addr)
                    server_settings["anon_list"][1].remove(command.split(" ")[1])
                    sock.sendto(message_encrypt(f'you were expelled!').encode('utf-8'), addr)
                    for i in server_settings['anon_list'][0]:
                        sock.sendto(message_encrypt(f' {command.split(" ")[1]} expelled!').encode('utf-8'), i)
                else:
                    sock.sendto(message_encrypt(f'у вас нет полномочий').encode('utf-8'), addres)

            elif "userlist" in command:
                sock.sendto(message_encrypt(f'{"  ".join(server_settings["anon_list"][1])}').encode('utf-8'), addres)

            else:
                sock.sendto(message_encrypt(f'команда не распознана').encode('utf-8'), addres)

        else:
            for i in server_settings['anon_list'][0]:
                if i == addres:
                    continue

                sock.sendto(data, i)


# добавление клиента к серверу
async def server_add_client(data, addres):
    global user_addr, user_name, server_settings
    client_text = data.decode('utf-8')
    if client_text.split(' ')[0] == "/connect":
        if client_text.split(' ')[1] != server_settings['server_password']:
            sock.sendto(message_encrypt('Доступ заблокирован').encode('utf-8'), addres)
        else:
            user_addr, user_name = addres, client_text.split(' ')[2]
            server_settings['anon_list'][0].append(user_addr)
            server_settings['anon_list'][1].append(user_name)
            sock.sendto(f'/connectTrue server starting in {time_run_server}'.encode('utf-8'), addres)
            print(f'connect {addres} {user_name}')
            for i in server_settings['anon_list'][0]:
                if i == addres:
                    continue
                sock.sendto(message_encrypt(f'connect {addres} {user_name}').encode('utf-8'), i)

    else:
        sock.sendto(message_encrypt('Доступ заблокирован').encode('utf-8'), addres)


# присоединение к чату/серверу
def Connect_server(server_ip, server_port, password):
    global server, sock, time_run_server
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))  # Задаем сокет как клиент
    alias = f'Anonim{random.randint(0, 10000)}'
    sock.sendto(f'/connect {password} {alias}'.encode('utf-8'), (server_ip, int(server_port)))
    data = sock.recv(1024)
    data_text = data.decode('utf-8')
    if '/connectTrue' in data_text:
        server = server_ip, int(server_port)
        # ключи
        time_run_server = data_text[32:]
        get_key()

        read_server = threading.Thread(target=potok_read_server)
        write_server = threading.Thread(target=potok_write_server)
        read_server.start()
        write_server.start()
        print('>>> ', end='')
    else:
        print("don't connect")


#  чтение сообщений от сервера
def potok_read_server():
    while 1:
        data = sock.recv(1024)
        data_text = data.decode('utf-8')
        data_text = message_decrypt(data_text)
        for i in range(4): sys.stdout.write('\b')
        print(f'{data_text}\n>>> ', end='')


# отправка сообщений на сервер
def potok_write_server():
    while 1:
        text = input()
        if text[:1] == '/':
            sock.sendto(text.encode('utf-8'), server)
            print('>>> ', end='')
        else:
            text = text + '    '
            text = message_encrypt(text)
            sock.sendto(text.encode('utf-8'), server)
            print('>>> ', end='')


if __name__ == '__main__':
    quest_start = input('Вы хотите:\n1. подключится к чяту\n2. создать чат\n>>> ')
    if quest_start == '1':  # подключение к чату
        server_ip_connect = input('ip от чата: ')
        server_port_connect = input('port от чата: ')
        password_connect = input('пароль от чата: ')
        Connect_server(server_ip_connect, server_port_connect, password_connect)
    elif quest_start == '2':  # создание чата
        server_ip = input('ip для чата: ')
        server_port = input('port для чата: ')
        server_password = input('пароль для подсоеденению к чату: ')
        asyncio.run(run_server(server_ip, server_port, server_password))
    else:
        print('функцыя не ясна')
