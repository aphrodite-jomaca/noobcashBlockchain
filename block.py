
import blockchain
from Crypto.Hash import SHA384
import config
from pymerkle import MerkleTree
import time

class Block:
	def __init__(self, previousHash, listOfTransactions, timestamp=None, hash=None, nonce=None):
		##set
		self.previousHash = previousHash
		self.timestamp = str(time()).encode() if timestamp == None else timestamp.encode()
		self.hash = hash
		self.nonce = nonce
		self.listOfTransactions = listOfTransactions
	

	def mine_block():
        merkleTree = MerkleTree()
        for transaction in self.listOfTransactions :
            merkleTree.encryptRecord(transaction.transaction_id.encode())
        merkleRoot = merkleTree.rootHash
    
        while(True):
			#https://www.gemini.com/cryptopedia/merkle-tree-blockchain-merkle-root
            #https://en.bitcoin.it/wiki/Block_hashing_algorithm
			nonce = randint(0,1000000)
            nonce = hex(nonce).encode()
            timestamp = str(time()).encode()
            header = self.previous_hash + nonce + merkleRoot + timestamp
            h = SHA256.new()
            
            computed_hash = h.new(h.new(header).digest()).hexdigest()
            computed_hash = str(computed_hash[::-1]) #little endian

            if int(computed_hash[0:config.DIFFICULTY],16) == 0 :
                break
        
		self.hash = computed_hash.encode()
		self.nonce = nonce
		self.timestamp = timestamp    


	def validate_currentHash(self):
        # validate block hash value
        

        merkleTree = MerkleTree()
        for transaction in self.listOfTransactions :
            merkleTree.encryptRecord(transaction.transaction_id.encode())
        merkleRoot = merkleTree.rootHash
        
        header = self.previousHash + self.nonce+ merkleRoot + self.timestamp

        h = SHA384.new()
        computed_hash = h.new(h.new(header).digest()).hexdigest()
        computed_hash = str(computed_hash[::-1]) 
        return (int(computed_hash[0:config.DIFFICULTY],16) == 0)

    def validate_block(self, state state):
		currentHashValid = self.validate_currentHash()
		prevHashValid = self.previousHash == state.blockchain[-1].hash

		return (currentHashValid and prevHashValid)

	def add_transaction(transaction transaction, state state):
		#add a transaction to the block
