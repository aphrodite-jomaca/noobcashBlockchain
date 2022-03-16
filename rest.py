import requests
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json

import block
import node
import blockchain
import wallet
import transaction
import wallet


### JUST A BASIC EXAMPLE OF A REST API WITH FLASK



app = Flask(__name__)
CORS(app)
blockchain = Blockchain()


#.......................................................................................



# get all transactions in the blockchain

# @app.route('/transactions/get', methods=['GET'])
# def get_transactions():
#     transactions = blockchain.transactions

#     response = {'transactions': transactions}
#     return jsonify(response), 200

@app.route('/bootstrap', methods=['GET'])
def start_bootstrap():
    
    return 

@app.route('/chain/length', methods=['GET'])
def get_chain_length():
    tsifsa = 'tsifsa' 

    response = {'length': tsifsa}
    return json.dumps(response)

@app.route('/chain/replace', methods=['GET'])
def get_chain():
    tsifsa = 'tsifsa' 

    response = {'chain': tsifsa}
    return json.dumps(response)

@app.route('/transaction', methods=['POST'])
def get_chain_length():
    
    return

@app.route('/block', methods=['POST'])
def get_chain_length():

    return


# run it once fore every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)