import requests
import json
import copy
import time
from flask import Flask, request, make_response
from argparse import ArgumentParser

import config
import miner
import utils
from node import Node
from block import Block
from transaction import Transaction


parser = ArgumentParser()
parser.add_argument('host', type=str) #the host of the address
parser.add_argument('port', type=int) #the port of the address
args = parser.parse_args()
app = Flask(__name__)

node = Node()

#------------------------------------------------------------------------------------------------

@app.route('/bootstrap/start', methods=['POST'])
def start_bootstrap():
    boot_data = json.loads(request.get_json())
    config.NODES = int(boot_data['NODES'])
    node.myid = 0
    node.create_wallet(boot_data['IP'], boot_data['PORT'])
    node.network_info.append({'id': 0, 'address': (boot_data['IP'], boot_data['PORT']), 'pub_key': node.wallet.public_key})
    node.genesis() # Create genesis block and transaction
    print("Genesis commensed")
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

        return make_response(json.dumps({'id' : node.current_id_count}),200)


@app.route('/node/start', methods=['POST'])
def start_node():
    node_data = json.loads(request.get_json())
    # Ids will be given later by bootstrap
    node.create_wallet(node_data['IP'], node_data['PORT'])
    # Node info will be given later by bootstrap
    info = json.dumps({'ip' : node_data['IP'], 'port' : node_data['PORT'], 'public_key' : node.wallet.public_key})
    response = requests.post('{}/bootstrap/register_node'.format('http://' + config.BOOTSTRAP_IP), json=info)
    if response.status_code != 200:
        print(str(response.status_code) + ': Problem sending my info to bootstrap')
        return make_response(json.dumps({'ip' : node_data['IP']}),response.status_code)

    node.myid = response.json()['id']
    return make_response(json.dumps({"id" : node.myid}), 201)

@app.route('/network_init', methods=['GET'])
def init_network():
    res = node.initialize_network()
    return make_response(json.dumps(res), 200)


@app.route('/network_info', methods=['POST'])
def receive_network_info():
    data = json.loads(request.get_json())

    with node.lock:
        node.update_network_info(data['network_info'])

        #first chain is genesis block --> no validation
        node.prev_val_utxos = copy.deepcopy(data['utxos'])
        node.curr_utxos = copy.deepcopy(data['utxos'])
        node.genesis_utxos = copy.deepcopy(data['utxos'])

        node.blockchain = [Block(**json.loads(block)) for block in data['chain']]
        for block in node.blockchain :
            block.listOfTransactions = [Transaction(**json.loads(t)) for t in block.listOfTransactions]
            block.nonce = str(block.nonce).encode()
            block.currentHash = str(block.currentHash).encode()
            block.previousHash = str(block.previousHash).encode()

            #there should be only ONE block
            node.genesis_block = block

    return make_response('Got all necessary info to start.',200)


@app.route('/block/receive', methods=['POST'])
def receive_block():
    block = Block(**json.loads(request.get_json()))
    block.listOfTransactions = [Transaction(**json.loads(t)) for t in block.listOfTransactions]
    block.nonce = str(block.nonce).encode()
    block.currentHash = str(block.currentHash).encode()
    block.previousHash = str(block.previousHash).encode()
    
    ret = miner.stop(node.miner_pid)
    node.total_trans_time = time.time()

    if ret != False:
        node.miner_pid = None
        with node.lock:
            res, flag = node.add_block(block)
            utils.statistics(node)
            if not res:
                print('Could not add block')
                if flag == 2:
                    return make_response('Invalid Info',400)
            else:
                print('Block Added')

            capacity_reached = node.check_mining()

        #in case of out-of order broadcasts of transactions
        #some trans may not be validated
        #try and find them from others
        for participant in node.network_info:
            if capacity_reached:
                break
            
            try:
                ip = participant['address'][0]
                port = participant['address'][1]
                address = ip + ':' + port

                response = requests.get('{}/{}'.format(address, 'transaction/queued'))
                if response.status_code != 200:
                    raise Exception('Failed to receive potential pending transactions.')

                pending_transactions = json.loads(response.json()['transactions'])

                with node.lock:
                    for t_json in pending_transactions:
                        t = Transaction(**json.loads(t_json))
                        ret = node.validate_transaction(t)

                    capacity_reached = node.check_mining()
            
            except Exception as e:
                print(e)

        if not capacity_reached:
            print('No new pending transactions, move on!')

    print('All transactions currently in the network: '+ str(len(node.all_trans_ids)))

    return make_response('Block received',200)
    

@app.route('/block/create', methods=['POST'])
def create_mined_block():
    data_json = request.get_json()
    node.miner_id = None
    data = json.loads(data_json)['block']
    node.total_trans_time = json.loads(data_json)['time']
    node.total_block_time += json.loads(data_json)['block_time']

    block = Block(**json.loads(data))
    block.listOfTransactions = [Transaction(**json.loads(t)) for t in block.listOfTransactions]
    block.nonce = str(block.nonce).encode()
    block.currentHash = str(block.currentHash).encode()
    block.previousHash = str(block.previousHash).encode()

    res, flag = node.add_block(block)
    utils.statistics(node)
    if not res:
        print('Could not add block')
        if flag == 2:
            return make_response('Invalid Info',400)
    else:
        if not (node.broadcast_block(block)):
            print('Could not broadcast block as a result of mining')
        print ('Successful mining and broadcast')

    print('All transactions currently in the network: '+ str(len(node.all_trans_ids)))

    return make_response('Block received',200)


@app.route('/chain/replace', methods=['GET'])
def get_chain():
    chain = [block.to_json() for block in node.blockchain]
    response = {'chain': chain} 
    return json.dumps(response)

@app.route('/chain/length', methods=['GET'])
def get_chain_length():
    chain_length = {'length' : len(node.blockchain)} 
    return json.dumps(chain_length)
    

@app.route('/transaction/receive', methods=['POST'])
def receive_transaction():
    trans = Transaction(**json.loads(request.get_json())) 
    node.validate_transaction(trans)
  
    node.check_mining()

    return make_response('Transaction received.',200)

@app.route('/transaction/queued', methods=['GET'])
def give_pending_transactions():
    pending_transactions = [t.to_json() for t in  node.wallet.transactions]
    response = {'transactions': json.dumps(pending_transactions)}
    return make_response(response)

# ------------------CLI------------------------

@app.route('/cli/transaction', methods=['POST'])
def post_transaction():
    if node.first == True:
        node.start_tp = time.time()
        node.first = False
    data = json.loads(request.get_json())
    try:
        amount = int(data['amount'])
    except:
        return make_response("Amount should be an integer", 400)
    if amount < 0:
        return make_response("Amount should be a positive integer", 400)

    if int(data['id']) >= config.NODES:
        return make_response('Invalid Node Id', 400)

    for participant in node.network_info:
        if participant['id'] == int(data['id']):
            pub = participant['pub_key']
    result = node.create_and_broadcast_transaction(pub, int(data['id']), int(data['amount']))
    if result == False:
        return make_response("Cannot create transaction!", 400)
    
    return make_response(json.dumps(result), 200) #TODO

@app.route('/cli/view', methods=['GET'])
def view_transaction():
    result = node.view_transactions()
    return make_response(json.dumps(result), 200) 

@app.route('/cli/balance', methods=['GET'])
def show_balance():
    balance = node.wallet.wallet_balance(node)
    if balance < 0:
        return make_response('Negative balance. WTF?', 200) 
    result = {'balance': balance}
    return make_response(json.dumps(result), 200)

@app.route('/cli/statistics', methods=['GET'])
def get_time_stats():
    avg_block_time, throughput = utils.statistics(node)
    
    result = {'avg_block_time': avg_block_time, 'throughput': throughput}
    return make_response(json.dumps(result), 200)


# run it once for every node
if __name__ == '__main__':
    app.run(host = args.host, port=args.port, debug = False,threaded = True)
