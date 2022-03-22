#!/usr/bin/env python3.6

import os
import requests
import argparse
import config
import sys


BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)
#--------------------------------------PARSE INPUT--------------------------------------------------

#difficulty, capacity and address of coordinator in config.py
parser = argparse.ArgumentParser()
parser.add_argument('host', help='IP Address (x.x.x.x) to be announced to bootstrap', type=str)
parser.add_argument('port', help='Port used', type=int)
parser.add_argument('-n', help='Number of nodes - only bootstrap', type=int)
args = parser.parse_args()

IP = 'http://{}:{}'.format(args.host, args.port)
IP_LOCAL = 'http://127.0.0.1:{}'.format(args.port)
PORT = str(args.port)
NODES = args.n



#----------------------------------------START------------------------------------------------------

try:
    url = '{}/bootstrap/start'.format(IP_LOCAL) if NODES else '{}/node/start'.format(HOST_LOCAL)
    json_data = {'NODES': NODES, 'IP': IP, 'PORT': PORT} if NODES else {'IP': IP, 'PORT': PORT}
    response = requests.post(url, json_data)
    if response.status_code != 200:
        raise Exception('{}: Could not connect to {}!'.format(response.status_code, IP))
except Exception as e:
    print(e)
    exit(-1)

#---------------------------------------COMMANDS----------------------------------------------------

# Enter main loop
while True:
    cli_input = input("(noob-cli)> ")
    print(cli_input)

    if cli_input.startswith('t'):
        # create a new transaction
        parts = cli_input.split()

        try:
            participants = requests.get(f'{HOST}/get_balance/').json()
            recepient = participants[parts[1]]['pubkey']
            amount = parts[2]
        except:
            continue

        API = f'{HOST}/create_transaction/'
        response = requests.post(API, {
            'token': TOKEN,
            'recepient': recepient,
            'amount': amount
        })

        if response.status_code == 200:
            print('OK.')
        else:
            print(f'Error: {response.text}')

    elif cli_input == 'view':
        # print list of transactions from last validated block
        API = f'{HOST}/get_transactions/'
        transactions = requests.get(API).json()['transactions']

        for tx in transactions:
            print(f'{tx["sender_id"]}\t->\t{tx["recepient_id"]}\t{tx["amount"]}\tNBC\t{tx["id"][:10]}')

    elif cli_input == 'balance':
        # print list of participants with their balance as of the last validated block
        balance = requests.get(f'{HOST}/get_balance/').json()

        for id, p in balance.items():
            print(f'{"* " if p["this"] else "  "}{id}\t({p["pubkey"][100:120]})\t{p["host"]}\t{p["amount"]}\tNBC')

    elif cli_input == 'help':
        help_message = ''
        print(help_message)

    elif cli_input == 'exit':
        exit(0)

    else:
        print('{}: Unknown command. Type `help`'.format(cli_input))