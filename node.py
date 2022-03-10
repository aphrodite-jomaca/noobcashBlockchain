import Block
import Wallet
import Transaction

from threading import RLock

class Node:
	def __init__(self, myid=None):
		##set
		self.blockchain = RLock()
		self.current_id_count = 0
		self.myid=myid

		#self.NBCs
		self.wallet = None
		self.network_info = []   #here we store information for every node, as its id, its address (ip:port) its public key and its balance 
		self.utxos = []



	def create_new_block():

	def create_wallet(self, ip, port):
		#create a wallet for this node, with a public key and a private key
		return Wallet((ip,port))

	def register_node_to_ring(self, info_list):
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bottstrap node informs all other nodes and gives the request node an id and 100 NBCs
		for info in info_list:
			if info['address'] == self.wallet.address:
				self.myid = info['id']
			else:
				self.network_info.append(info)


	def create_transaction(receiver, signature, amount):
		sender = self.wallet.public_key
        inputs = []

        #Check if we have enough money
        current_balance = 0
        utxos_to_remove = []

        for utxo in self.utxos[sender]:
            current_balance += utxo['amount']
            inputs.append(utxo['transaction_id'] + ':' + utxo['type'])
            utxos_to_remove.append(utxo)

            if current_balance >= amount :
                break 
        
        if current_balance < amount:
            print('NBCs in wallet not enough! Requested ', amount, 'but have', coins, '!')
            return (False)

        for utxo in utxos_to_remove: 
            self.utxos[sender].remove(utxo)

        #If yes, create transaction
        trans = Transaction(sender, receiver, amount, inputs)
        trans.create_transaction_id()
        trans.sign_transaction(self.wallet.private_key)

        #Create corresponding outputs
		outputs = [{
                'transaction_id': trans.transaction_id,
                'type' : 0,
                'recipient': trans.recipient_address,
                'amount': trans.amount
			}]

        if (current_balance > trans.amount):  
            outputs.append({
                'transaction_id': trans.transaction_id,
                'type' : 1,
                'recipient': trans.sender_address,
                'amount': current_balance - trans.amount
            })


		trans.transaction_outputs = outputs

        for output in outputs:
			if sender not in self.utxos : self.utxos[sender] = []
			self.utxos[sender].append(output)

        #.transactions.append() ???

        return trans


	def broadcast_transaction():





	def validdate_transaction():
		#use of signature and NBCs balance


	def add_transaction_to_block():
		#if enough transactions  mine



	def mine_block():



	def broadcast_block():


		

	def valid_proof(.., difficulty=MINING_DIFFICULTY):




	#concencus functions

	def valid_chain(self, chain):
		#check for the longer chain accroose all nodes


	def resolve_conflicts(self):
		#resolve correct chain



