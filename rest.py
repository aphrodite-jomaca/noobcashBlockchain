import requests
from flask import Flask, request, Blueprint, make_response
from flask_cors import CORS
import json

from node import Node
from block import Block
from transaction import Transaction
import config


### JUST A BASIC EXAMPLE OF A REST API WITH FLASK



app = Flask(__name__)
# CORS(app)

node = Node()


#.......................................................................................

# get all transactions in the blockchain

# @app.route('/transactions/get', methods=['GET'])
# def get_transactions():
#     transactions = blockchain.transactions

#     response = {'transactions': transactions}
#     return jsonify(response), 200

@app.route('/bootstrap/start', methods=['POST'])
def start_bootstrap():
    boot_data = json.loads(request.get_json())
    config.DIFFICULTY = int(boot_data['DIFFICULTY'])
    config.CAPACITY = int(boot_data['CAPACITY'])
    config.NODES = int(boot_data['NODES'])
    node.myid = 0
    node.create_wallet(boot_data['IP'], boot_data['PORT'])
    node.network_info.append({'id': 0, 'address': (boot_data['IP'], boot_data['PORT']), 'pub_key': node.wallet.public_key})
    node.genesis() # Create genesis block and transaction
    
    return make_response(json.dumps({"id" : node.myid}), 201)


@app.route('/bootstrap/register_node', methods=['POST'])
def register_node():
        data = json.loads(request.get_json())
        node_ip = data['ip']
        node_port = data['port']
        node_pub = data['public_key']
        if (not node_ip or not node_port or not node_pub):
            return "Missing Info", 400

        node.current_id_count += 1 
        print('Given ID is:', node.current_id_count)
        node.curr_utxos[node_pub] = []
        node.prev_val_utxos[node_pub] = []

        node.network_info.append({'id': node.current_id_count, 'address': (node_ip, node_port), 'pub_key': node_pub})

        if (node.current_id_count == config.NODES - 1) :
            node.initialize_network()
        return make_response(json.dumps({'id' : node.current_id_count}),200)


@app.route('/node/start', methods=['POST'])
def start_node():
    node_data = json.loads(request.get_json())
    config.DIFFICULTY = int(node_data['DIFFICULTY'])
    config.CAPACITY = int(node_data['CAPACITY'])
    # Ids will be given later by bootstrap
    node.create_wallet(node_data['IP'], node_data['PORT'])
    # Node info will be given later by bootstrap
    info = json.dumps({'ip' : node_data['IP'], 'port' : node_data['PORT'], 'public_key' : node.wallet.public_key})
    response = requests.post('{}/bootstrap/register_node'.format(node_data['BOOTSTRAP_IP']), json=info)
    if response.status_code != 200:
        print(response.status_code+': Problem sending my info to bootstrap')
        return make_response(json.dumps({'ip' : node_data['IP']}),response.status_code)

    node.myid = response.json()['id']
    return make_response(json.dumps({"id" : node.myid}), 201)


@app.route('/network_info', methods=['POST'])
def receive_network_info():
    data = json.loads(request.get_json())
    node.update_network_info(data['network_info'])

    #first chain is genesis block --> no validation
    
    node.prev_val_utxos = data['utxos']
    node.curr_utxos = node.prev_val_utxos

    node.blockchain = [Block(**json.loads(block)) for block in data['chain']]
    for block in node.blockchain :
        block.listOfTransactions = [Transaction(**json.loads(t)) for t in block.listOfTransactions]
        block.nonce = str(block.nonce).encode()
        block.currentHash = str(block.currentHash).encode()
        block.previousHash = str(block.previousHash).encode()

    return make_response('Got all necessary info to start.',200)


@app.route('/block', methods=['POST'])
def get_chain_length():

    return


@app.route('/chain/replace', methods=['GET'])
def get_chain():
    tsifsa = 'tsifsa' 

    response = {'chain': tsifsa}
    return json.dumps(response)

@app.route('/transaction', methods=['POST'])
def receive_transaction():
    trans = Transaction(**json.loads(request.get_json())) 
    return_val = Transaction.validate_transaction(trans)
    # State.state.coin_distribution()
    if (len(node.wallet.transactions) >= config.CAPACITY):
        print('Node '+ node.myid + ' mining...')
        trans_ids = [t.transaction_id for t in node.wallet.transactions]
        print(trans_ids)
        node.mine_and_broadcast_block()

    return make_response('Transaction received.',200)


@app.route('/block', methods=['POST'])
def receive_block():
   

    return

@app.route('/cli/transaction', methods=['POST'])
def post_transaction():
    data = json.loads(request.get_json())
    try:
        amount = int(data['amount'])
    except:
        return make_response("Amount should be an integer", 400)
    if amount < 0:
        return make_response("Amount should be a positive integer", 400)

    if data['id'] >= config.NODES:
        return make_response('Invalid Node Id', 400)

    for node in node.network_info:
        if node['id'] == data['id']:
            pub = node['pub_key']
    result = node.create_and_broadcast_transaction(pub, data['id'], data['amount'])

    return make_response(json.dumps(result), 200) #TODO


# run it once fore every node

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)