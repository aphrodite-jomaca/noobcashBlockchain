import os, sys
import json
import requests

from subprocess import Popen
from signal import SIGTERM
import time


from block import Block
from transaction import Transaction

def start_your_engines_and_may_the_best_woman_WIN(miner_pid, address, block):

    try:
        os.kill(miner_pid, 0)
        print(f'Miner with pid {miner_pid} is running.')
        return True
    except:
        try:
            print('Mining...')
            miner = Popen(['python3.6', __file__, address, block.to_json()])
            return miner.pid

        except Exception as e:
            print(f'Miner failed: {e}')
            return False

def stop(miner_pid):
    try:
        if miner_pid != None:
            print('Stop miner with pid', miner_pid)
            os.kill(miner_pid, SIGTERM)
            return None
        else:
            return True
    except OSError as e:
        print(f'Problem stopping miner: {e.errno}: {e}')
        return False
    except Exception as e:
        print(f'Problem stopping miner: {e}')
        return False


def mine_and_announce(address, block_json):
    block = Block(**json.loads(block_json))
    block.listOfTransactions = [Transaction(**json.loads(t)) for t in block.listOfTransactions]
    block.nonce = str(block.nonce).encode()
    block.currentHash = str(block.currentHash).encode()
    block.previousHash = str(block.previousHash).encode()

    block.mine_block()

    json_data = {'block': block.to_json(), 'time': time.time()}

    response = requests.post('{}/{}'.format(address, 'block/create'), json=json.dumps(json_data))

    if response.status_code != 200:
        print(f'Announcing block failed: {response.text}')

    return

if __name__ == '__main__':
    mine_and_announce(sys.argv[1], sys.argv[2])
