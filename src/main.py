import json
import os
import random
import time
import re

import boto3

import requests

print('Loading function')

token = os.environ['tg_token']
baseUrl = f'https://api.telegram.org/bot{token}'

dynamodb_table = os.environ['dynamodb_table']
client = boto3.client('dynamodb')

min_length = 1
min_circum = 1
cum_regen_cooldown = 20 * 60


def send_message(message, chat_id):
    params = {
        'chat_id': chat_id,
        'text': message
    }
    requests.post(url=baseUrl + '/sendMessage', params=params)


def set_commands():
    data = {
        'lang_code': 'ua-uk',
        'commands': '''[
            {"command": "check", "description": "Глянути на песюн"}, 
            {"command": "cum", "description": "Ух ох"}
            ]'''
    }
    requests.post(url=baseUrl + '/setMyCommands', data=data)


def get_penus_info(chat_id, user_id):
    resp = client.get_item(
        TableName=dynamodb_table,
        Key={
            "chatId": {
                'S': str(chat_id)
            },
            "userId": {
                'S': str(user_id)
            }
        }
    )

    item = {"chatId": chat_id, "userId": user_id}
    if "Item" in resp:
        if 'length' in resp['Item']:
            item['length'] = resp['Item']['length']['N']
        if 'circum' in resp['Item']:
            item['circum'] = resp['Item']['circum']['N']
        if 'last_cum' in resp['Item']:
            item['last_cum'] = resp['Item']['last_cum']['S']
    return item


def update_penus_info(info):

    client.update_item(
        TableName=dynamodb_table,
        Key={
            "chatId": {
                'S': str(info['chatId'])
            },
            "userId": {
                'S': str(info['userId'])
            }
        },
        AttributeUpdates={
            "length": {
                'Value': {
                    'N': str(info.get('length', str(min_length)))
                }
            },
            "circum": {
                'Value': {
                    'N': str(info.get('circum', str(min_circum)))
                }
            },
            "last_cum": {
                'Value': {
                    'S': str(info.get('last_cum', '0'))
                }
            }
        }
    )


def get_delta_phrase(d):
    if d == 0:
        return "не змінилась"
    if d > 0:
        return f"виріс на {d}см💪"
    else:
        return f"зменшилась на {d}см🤣"


def get_penus_status_message_with_delta(leng, cir, dlen, dcir, user_name):
    len_phrase = get_delta_phrase(dlen)
    cir_phrase = get_delta_phrase(dcir)

    return f'''Опа😳, 
    @{user_name} 🐓пенус🐓 має довжину {leng}см({len_phrase}), окружність {cir}см({cir_phrase})'''


def get_penus_status_message_new(user_name):
    return f'''Ого😳, 
    @{user_name} перший раз дивиться на пенус?? Довжина {min_length}см, окружність {min_circum}см'''


def grow(max_growth, min_size, curr_val):
    delta = random.randrange(max(-(curr_val - min_size), -max_growth), max_growth)
    return delta


def check_penus(chat_id, user_id, user_name):
    item = get_penus_info(chat_id, user_id)

    if "length" in item:
        length_old = int(item.get('length', min_length))
        circum_old = int(item.get('circum', min_circum))

        dlen = grow(10, min_length, length_old)
        dcir = grow(9, min_circum, circum_old)

        item['length'] = length_old + dlen
        item['circum'] = circum_old + dcir
        send_message(get_penus_status_message_with_delta(item['length'], item['circum'], dlen, dcir, user_name),
                     chat_id)
    else:
        item['length'] = min_length
        item['circum'] = min_circum
        send_message(get_penus_status_message_new(user_name), chat_id)

    update_penus_info(item)


def cum(chat_id, user_id, user_name):
    info = get_penus_info(chat_id, user_id)

    last_cum = info.get('last_cum', 0)
    if int(last_cum) + cum_regen_cooldown > int(time.time()):
        send_message(f"АХАХХАХАХАХАХХА @{user_name} не зміг😖", chat_id)
        return

    info['last_cum'] = int(time.time())
    update_penus_info(info)
    send_message(f"Ух ох @{user_name} 💦💦💦💦💦💦💦💦💦💦💦💦", chat_id)


def handle_command(command, body):
    message_root = body.get("message")
    if not message_root:
        message_root = body.get("my_chat_member")
    chat_id = message_root['chat']['id']
    user_id = message_root['from']['id']
    user_name = message_root['from']['username']

    if command == '/start':
        set_commands()
        send_message(f"Привет @{user_name}", chat_id)

    if command == '/check':
        check_penus(chat_id, user_id, user_name)

    if command == '/cum':
        cum(chat_id, user_id, user_name)


def lambda_handler(event, context):

    body_str = event['body']
    print(body_str)

    body = json.loads(body_str)
    if "message" not in body:
        print("no message in body")
        return

    if "text" not in body["message"]:
        print("no text")
        return

    command = body["message"]['text']
    commands = re.findall("^/[a-zA-Z]*", command)
    if not commands:
        print("no command")
        return
    command = commands[0]
    print(f"Command {command}")
    handle_command(command, body)

    return json.dumps(event)
