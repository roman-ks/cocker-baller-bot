import json
import os

import requests

print('Loading function')

token = os.environ['tg_token']
baseUrl = f'https://api.telegram.org/bot{token}'


def send_message(message, chat_id):
    params = {
        'chat_id': chat_id,
        'text': message
    }
    resp = requests.post(url=baseUrl + '/sendMessage', params=params)
    print(resp.content)


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event))
    body_str = event['body']
    print(body_str)

    body = json.loads(body_str)

    chat_id = body['message']['chat']['id']
    send_message("Hello", chat_id)
    return json.dumps(event)
    # raise Exception('Something went wrong')


input = open("input.json", "r+")
text = input.read()
print(f"File: {text}")
lambda_handler(json.loads(text), {})
input.close()
