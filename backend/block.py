from Crypto.Hash import SHA256
import config
from pymerkle import MerkleTree
import time
from random import randint
from copy import deepcopy
import json

class Block:
    def __init__(self, index, previousHash, listOfTransactions, timestamp=None, currentHash=None, nonce=None):
    ##set
        self.index = index
        self.previousHash = previousHash
        self.timestamp = str(time.time()).encode() if timestamp == None else timestamp.encode()
        self.currentHash = currentHash
        self.nonce = nonce
        self.listOfTransactions = listOfTransactions

    def to_json(self):
        block_dict = deepcopy(self.__dict__)
        block_dict['listOfTransactions'] = [transaction.to_json() for transaction in block_dict['listOfTransactions']]
        block_dict['previousHash'] = block_dict['previousHash'].decode("utf-8") if type(block_dict['previousHash']) == bytes else block_dict['previousHash']
        block_dict['currentHash'] = block_dict['currentHash'].decode("utf-8") if type(block_dict['currentHash']) == bytes else block_dict['currentHash']
        block_dict['timestamp'] = block_dict['timestamp'].decode("utf-8") if type(block_dict['timestamp']) == bytes else block_dict['timestamp']
        block_dict['nonce'] = block_dict['nonce'].decode("utf-8") if type(block_dict['nonce']) == bytes else block_dict['nonce'] 
        return json.dumps(block_dict)

    def mine_block(self):
        merkleTree = MerkleTree()
        for transaction in self.listOfTransactions :
            merkleTree.encryptRecord(transaction.transaction_id.encode())
            merkleRoot = merkleTree.rootHash

        while(True):
        # https://www.gemini.com/cryptopedia/merkle-tree-blockchain-merkle-root
        # https://en.bitcoin.it/wiki/Block_hashing_algorithm
            nonce = randint(0,1000000)
            nonce = hex(nonce).encode()
            timestamp = str(time.time()).encode()
            header = hex(self.index).encode() + self.previousHash + nonce + merkleRoot + timestamp
            h = SHA256.new()

            computed_hash = h.new(h.new(header).digest()).hexdigest()
            computed_hash = str(computed_hash[::-1]) #little endian

            if int(computed_hash[0:config.DIFFICULTY],16) == 0 :
                break

        self.currentHash = computed_hash.encode()
        self.nonce = nonce
        self.timestamp = timestamp    
        return 

    def validate_currentHash(self):
    # validate block hash value
        merkleTree = MerkleTree()
        for transaction in self.listOfTransactions :
            merkleTree.encryptRecord(transaction.transaction_id.encode())
            merkleRoot = merkleTree.rootHash

        header = hex(self.index).encode() + self.previousHash + self.nonce+ merkleRoot + self.timestamp

        h = SHA256.new()
        computed_hash = h.new(h.new(header).digest()).hexdigest()
        computed_hash = str(computed_hash[::-1]) 
        return (int(computed_hash[0:config.DIFFICULTY],16) == 0)
        
    def validate_previousHash(self, blockchain):
        return self.previousHash == blockchain[-1].currentHash

    def validate_block(self, blockchain):
        currentHashValid = self.validate_currentHash()
        prevHashValid = self.validate_previousHash(blockchain)

        return (currentHashValid and prevHashValid)

    # def add_transaction(transaction transaction, state state):
    # #add a transaction to the block
