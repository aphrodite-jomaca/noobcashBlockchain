#!/usr/bin/env python3.6

import os
import requests
import argparse
import sys
import json


BASE_DIR = os.path.dirname(__file__)
sys.path.append(BASE_DIR)
#--------------------------------------PARSE INPUT--------------------------------------------------

#difficulty, capacity and address of coordinator in config.py
parser = argparse.ArgumentParser()
parser.add_argument('host', help='IP Address (x.x.x.x) to be announced to bootstrap', type=str)
parser.add_argument('port', help='Port used', type=int)
parser.add_argument('-n', help='Number of nodes - only bootstrap', type=int)
args = parser.parse_args()

IP = 'http://{}'.format(args.host)
IP_LOCAL = 'http://{}:{}'.format(args.host, args.port)
PORT = str(args.port)
NODES = args.n



#----------------------------------------START------------------------------------------------------

try:
    url = '{}/bootstrap/start'.format(IP_LOCAL) if NODES else '{}/node/start'.format(IP_LOCAL)
    json_data = {'NODES': NODES, 'IP': IP, 'PORT': PORT} if NODES else {'IP': IP, 'PORT': PORT}
    response = requests.post(url, json = json.dumps(json_data))
    if not str(response.status_code).startswith('2'):
        raise Exception('{}: Could not connect to {}!'.format(response.status_code, IP))
except Exception as e:
    print(e)
    exit(-1)

#---------------------------------------COMMANDS----------------------------------------------------

while True:
    cli_input = input("(noob-cli)> ").strip()
    print(cli_input)

    if cli_input.startswith('t '):
        try:
            keyword, rec_id, amount = cli_input.split()
        except ValueError as e:
            print('Input should be `t <recipient_id> <amount>')
            continue

        url = '{}/cli/transaction'.format(IP_LOCAL)
        json_data = {'id': rec_id, 'amount': amount}

        response = requests.post(url, json=json.dumps(json_data))

        if response.status_code == 200:
            print('Transaction Complete.')
        else:
            print('Problem completing transaction: {}'.format(response.text))

    elif cli_input == 'view':
        url = '{}/cli/view'.format(IP_LOCAL)
        transactions = requests.get(url).json()['transactions']

        for t in transactions:
            print('{}:  Sender: {}, Recipient: {}, Amount: {} NBCs.'.format(t['transaction_id'][:10], t['sender_address'], t['recipient_address'], t['amount']))

    elif cli_input == 'balance':
        url = '{}/cli/balance'.format(IP_LOCAL)
        balance = requests.get(url).json()['balance']

        print('You have {} NBCs left.'.format(balance))
    
    elif cli_input.startswith('test'):
        try:
            keyword, filename = cli_input.split()
        except ValueError as e:
            print("Input should be `test <filename>`")

        try:
            with open(filename, 'r') as fin:
                for line in fin:
                    id, amount = line.split()
                    rec_id = id[2:]

                    url = '{}/cli/transaction'.format(IP_LOCAL)
                    json_data = {'id': rec_id, 'amount': amount}

                    response = requests.post(url, json=json.dumps(json_data))

                    if response.status_code == 200:
                        print('Transaction Complete.')
                    else:
                        print('Problem completing transaction: {}'.format(response.text))
                print('All transactions sent. Wait until finished to get stats.')
        except Exception as e:
            print('Problem opening file: {}'.format(e))
            
    elif cli_input == 'stats':
        url = '{}/cli/statistics'.format(IP_LOCAL)
        response = requests.get(url).json()
        avg_block_time = response['avg_block_time']
        throughput = response['throughput']

        print('Average Block time: {}, Throughput: {}.'.format(avg_block_time, throughput))

    elif cli_input == 'help':
        help_message = '''
        Usage:
        cli.py <HOST_IP> <PORT> -n <NODES>  Start bootstrap node with NODES number of nodes
        cli.py <HOST_IP> <PORT>             Start simple node
        
       Commands:
        `t <RECIPIENT_ID> <AMOUNT>`         Send AMOUNT NBCs to recipient with id: RECIPIENT_ID
        `view`                              View all valid transactions from the last block
        `balance`                           View your own balance
        `test <FILENAME>`                   Run tests in FILENAME
        `stats`                             View average block time and throughput after tests
        `help`                              Help message
        `exit`                              Exit NOOB-CLI
        '''
        print(help_message)

    elif cli_input == 'exit':
        exit(0)

    else:
        print('{}: Unknown command. Type `help`'.format(cli_input))
