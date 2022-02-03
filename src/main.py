import json
import os
import random

import boto3

import requests

print('Loading function')

token = os.environ['tg_token']
baseUrl = f'https://api.telegram.org/bot{token}'

dynamodb_table = os.environ['dynamodb_table']
client = boto3.client('dynamodb')

min_length = 1
min_circum = 1

def send_message(message, chat_id):
    params = {
        'chat_id': chat_id,
        'text': message
    }
    resp = requests.post(url=baseUrl + '/sendMessage', params=params)
    print(resp.content)


def set_commands():
    data = {
        'lang_code': 'ua-uk',
        'commands': '''[
            {"command": "check", "description": "Глянути на песюн"}, 
            {"command": "cum", "description": "Ух ох"}
            ]'''
    }
    resp = requests.post(url=baseUrl + '/setMyCommands', data=data)
    print(resp.content)


def get_penus_info(chat_id, user_id):
    item = client.get_item(
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

    print(f"Dynamodb item: {item}")
    return item


def update_penus_info(info):
    print(f"new penus info: {info}")

    resp = client.update_item(
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
                    'N': str(info['length'])
                }
            },
            "circum": {
                'Value': {
                    'N': str(info['circum'])
                }
            }
        }
    )

    print(f"dynamodb update response {resp}")


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
    delta = random.randrange(max(-(curr_val-min_size), -max_growth), max_growth)
    return delta


def check_penus(chat_id, user_id, user_name):
    info = get_penus_info(chat_id, user_id)

    item = {"chatId": chat_id, "userId": user_id}
    if "Item" in info:
        print(f"found: {info}")
        item['length'] = info['Item']['length']['N']
        item['circum'] = info['Item']['circum']['N']

        length_old = int(item.get('length', min_length))
        circum_old = int(item.get('circum', min_circum))

        print(f"Old vals, {length_old},{circum_old}")
        dlen = grow(10, min_length, length_old)
        dcir = grow(9, min_circum, circum_old)
        print(f"D vals, {dlen},{dcir}")

        item['length'] = length_old + dlen
        item['circum'] = circum_old + dcir
        send_message(get_penus_status_message_with_delta(item['length'], item['circum'], dlen, dcir, user_name),
                     chat_id)
    else:
        print("Not found in Dynamo")
        item['length'] = min_length
        item['circum'] = min_circum
        send_message(get_penus_status_message_new(user_name),chat_id)

    print(f"New vals, {item['length']},{item['circum']}")
    update_penus_info(item)


def handle_command(command, body):
    chat_id = body['message']['chat']['id']

    if command == '/start':
        set_commands()

    if command == '/check':
        check_penus(chat_id, body['message']['from']['id'], body['message']['from']['username'])

    if command == '/cum':
        send_message("Пішла кумка лол", chat_id)


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    body_str = event['body']
    print(body_str)

    body = json.loads(body_str)
    command = body['message']['text']
    handle_command(command, body)

    return json.dumps(event)

