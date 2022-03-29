from block import Block
from wallet import Wallet
from transaction import Transaction
import time
import requests
import copy
import utils
import config
import miner
import json

from threading import RLock

class Node:
	def __init__(self, myid=None):
		##set
		self.lock = RLock()
		self.blockchain = []
		self.current_id_count = 0
		self.myid=myid
		self.miner_pid = None
		self.wallet = None
		self.network_info = []   #here we store information for every node, as its id, its address (ip:port) its public key and its balance 
		self.curr_utxos = {}
		self.prev_val_utxos = {}
		self.genesis_block = None
		self.genesis_utxos = None
		self.total_block_time = 0
		self.all_trans_ids = set()
		self.total_trans_time = 0
		self.first = True
		self.start_tp = 0


	def create_wallet(self, ip, port):
		#create a wallet for this node, with a public key and a private key
		self.wallet = Wallet((ip,port))

	def update_network_info(self, info_list):
		#add this node to the ring, only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
		#bootstrap node informs all other nodes and gives the request node an id and 100 NBCs
		with self.lock:
			for info in info_list:
				if info['address'] == self.wallet.address:
					self.myid = info['id']

				self.network_info.append(info)
		return
				
	
	def genesis(self):
		genesis_transaction = Transaction(0, self.wallet.public_key, 100*config.NODES, [])
		genesis_transaction.create_transaction_id()
		
		genesis_utxo = [{
			'transaction_id' : genesis_transaction.transaction_id, 
			'type' : 0, 
			'recipient' : genesis_transaction.recipient_address , 
			'amount' : genesis_transaction.amount }]
		genesis_transaction.transaction_outputs = [genesis_utxo]
		
		# First VALID block
		genesis_block = Block(1, b'1', [genesis_transaction], nonce = 0,currentHash = b'1')
		self.genesis_block = copy.deepcopy(genesis_block)

		self.curr_utxos[self.wallet.public_key] = genesis_utxo
		self.prev_val_utxos = copy.deepcopy(self.curr_utxos)
		self.genesis_utxos = copy.deepcopy(self.curr_utxos)

		self.blockchain.append(genesis_block)
		return 
		

	def create_transaction(self, receiver, amount):
		sender = self.wallet.public_key
		inputs = []
		if sender == receiver:
			print("You cannot give money to yourself!")
			return False
		existent_sender = False
		existent_recipient = False
		for node in self.network_info:
			if node['pub_key'] == sender:
				existent_sender = True
			if node['pub_key'] == receiver:
				existent_recipient = True 
		if existent_sender == False:
			print('Unknown sender!')
			return False
		if existent_recipient == False:
			print('Unknown recipient!')
			return False
		if amount <= 0:
			print('Amount should be positive!')
			return False
        #Check if we have enough money
		current_balance = 0
		utxos_to_remove = []
		
		for utxo in self.curr_utxos[sender]:
			current_balance += utxo['amount']
			inputs.append(utxo['transaction_id'] + ':' + str(utxo['type']))
			utxos_to_remove.append(utxo)
			
			if current_balance >= amount :
				break 
        
		if current_balance < amount:
			print('NBCs in wallet not enough! Requested ', amount, 'but have', current_balance, '!')
			return False
			
		
		for utxo in utxos_to_remove: 
			self.curr_utxos[sender].remove(utxo)

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
			if output['recipient'] not in self.curr_utxos : self.curr_utxos[output['recipient']] = []
			self.curr_utxos[output['recipient']].append(output)
		
		self.wallet.transactions.append(trans)
		self.all_trans_ids.add(trans.transaction_id)
		# print("----------------CREATE--------------------")
		# print("Inputs: ",inputs)
		# for pub in self.curr_utxos:
		# 	print(pub[80:100])
		# 	for utxo in self.curr_utxos[pub]:
		# 		print(utxo['transaction_id'][:10])
		# 		print(utxo['type'])
		# 		print(utxo['recipient'][80:100])
		# 		print(utxo['amount'])
		# 		print()
		# 	print("---------------------------------------")
		return trans

	def validate_transaction(self, transaction):
		#use of signature and NBCs balance
		try:
			with self.lock:
				self.all_trans_ids.add(transaction.transaction_id)
				if transaction in self.wallet.transactions:
					return False
				if transaction.sender_address == transaction.recipient_address:
					raise Exception('You cannot send money to yourself!')
				existent_sender = False
				existent_recipient = False
				for node in self.network_info:
					if node['pub_key'] == transaction.sender_address:
						existent_sender = True
					if node['pub_key'] == transaction.recipient_address:
						existent_recipient = True 
				if existent_sender == False:
					raise Exception('Unknown sender!')
				if existent_recipient == False:
					raise Exception('Unknown recipient!')
				if transaction.amount <= 0:
					raise Exception('Amount should be positive!')

				valid_signature = transaction.verify_signature()
				if not valid_signature:
					raise Exception('Invalid Signature!')
				
		except Exception as e:	
			print(str(e))	
			return False

		#try finding each input in UTXOs and check if enough money exists
		try :
			with self.lock:
				current_balance = 0
				utxos_to_remove = []
				for trans_input in transaction.transaction_inputs: 
					present = False  
					for utxo in self.curr_utxos[transaction.sender_address]:
						utxo_combined_id = utxo['transaction_id'] + ':' + str(utxo['type'])
						if utxo_combined_id == trans_input and utxo['recipient'] == transaction.sender_address: 
							present = True
							current_balance += utxo['amount']
							utxos_to_remove.append(utxo)
							break

					#bug detected / wrong inputs
					if not present:
						raise Exception('Cannot find Transaction Input in UTXOs')
						
				#detected double spending
				if current_balance < transaction.amount:
					raise Exception('Sender does not have enough NBCs!')
		except Exception as e:

			print(str(e))
			return False
		
		for utxo in utxos_to_remove: 
			self.curr_utxos[utxo['recipient']].remove(utxo)

		#Create corresponding outputs
		outputs = [{
				'transaction_id': transaction.transaction_id,
				'type' : 0,
				'recipient': transaction.recipient_address,
				'amount': transaction.amount
			}]

		if (current_balance > transaction.amount):  
			outputs.append({
				'transaction_id': transaction.transaction_id,
				'type' : 1,
				'recipient': transaction.sender_address,
				'amount': current_balance - transaction.amount
			})


		transaction.transaction_outputs = outputs

		for output in outputs:
			if output['recipient'] not in self.curr_utxos : self.curr_utxos[output['recipient']] = []
			self.curr_utxos[output['recipient']].append(output)

		self.wallet.transactions.append(transaction)
		
		# print("-----------VALIDATE----------")
		# print("Inputs: ", transaction.transaction_inputs)
		# for pub in self.curr_utxos:
		# 	print(pub[80:100])
		# 	for utxo in self.curr_utxos[pub]:
		# 		print(utxo['transaction_id'][:10])
		# 		print(utxo['type'])
		# 		print(utxo['recipient'][80:100])
		# 		print(utxo['amount'])
		# 		print()
		# 	print("------------------------------")
		return True
			
	def view_transactions(self):
		last_valid_block = self.blockchain[-1]
		valid_trans = copy.deepcopy(last_valid_block.listOfTransactions)

		key_dict = {}
		for node in self.network_info:
			key_dict[node['pub_key']] = node['id']

		for trans in valid_trans:
			pub_sender = trans.sender_address
			pub_recipient = trans.recipient_address
			trans.sender_address = key_dict[pub_sender]
			trans.recipient_address = key_dict[pub_recipient]
		transactions = {'transactions': [t.to_json() for t in valid_trans]}

		return transactions

	def broadcast_transaction(self, transaction):
		utils.broadcast(transaction.to_json(), 'transaction/receive', self.network_info, self.myid)
		return True
	
	def broadcast_block(self, block):
		utils.broadcast(block.to_json(), 'block/receive', self.network_info, self.myid)
		return True

	def create_and_broadcast_transaction(self, receiver_key, receiver_id, amount):
		print("Transaction: {} gives {} to {}!".format(self.myid, amount, receiver_id))
		transaction = self.create_transaction(receiver_key,amount)
		if transaction == False:
			return transaction

		result = self.broadcast_transaction(transaction)

		#check if we need to mine 
		result = self.check_mining()
		return result

	def check_mining(self):
		if len(self.wallet.transactions) >= config.CAPACITY:
			print('Node '+ str(self.myid) + ' mining...')
			trans_ids = [t.transaction_id[:10] for t in self.wallet.transactions]
			print(trans_ids)
			result = self.start_mining()
			return result


	def initialize_network(self):
		# broadcast info ring to all nodes 
		# including initial chain (genesis block only)
		# utxos as formed until now
		data = {'chain': [block.to_json() for block in self.blockchain], 
				'network_info': self.network_info,
				'utxos': self.prev_val_utxos}

		utils.broadcast(json.dumps(data), 'network_info', self.network_info, self.myid)		

		#make initial transactions of 100 NBCs
		for node in self.network_info:
			if node['id'] == self.myid:
				continue
			result = self.create_and_broadcast_transaction(node['pub_key'], node['id'], 100)

		return result
		
	def start_mining(self):
		# copy_trans = deepcopy(self.transactions) 
		for node in self.network_info:
			if node['id'] == self.myid:
				ip = node['address'][0]
				port = node['address'][1]
				address = ip + ':' + port

		trans = self.wallet.transactions[0:config.CAPACITY]
		block = Block(len(self.blockchain)+1, self.blockchain[-1].currentHash, trans)
		result = miner.start_your_engines_and_may_the_best_woman_WIN(self.miner_pid, address, block)

		if result == False or result == True:
			return False
		else:
			self.miner_pid = result
			return True


	#consensus functions
	def validate_chain(self, blockchain, transactions):
		with self.lock:
			# restart from genesis block
			self.blockchain = [self.genesis_block]
			self.curr_utxos = copy.deepcopy(self.genesis_utxos)
			self.prev_val_utxos = copy.deepcopy(self.genesis_utxos)

			self.wallet.transactions = []

			# valid chain = valid blocks  (Appendable) and valid transactions in queue
			for block in blockchain:
				# updates transactions in queue
				res = self.add_block(block)
				if not res:
					return False

			for t in transactions:
				self.validate_transaction(t)

			return True

	def add_block(self, block):
		with self.lock:
			try:
				# save me
				# please
				#start_time = time.time()
				TRANSACTIONS_BACKUP = copy.deepcopy(self.wallet.transactions)
				UTXOS_BACKUP = copy.deepcopy(self.curr_utxos)
				BLOCKCHAIN_BACKUP = copy.deepcopy(self.blockchain)
				VALID_UTXOS_BACKUP = copy.deepcopy(self.prev_val_utxos)

				previous_block = self.blockchain[-1]
				
				if block.index != previous_block.index+1:
					print('different index')
				if len(block.listOfTransactions) != config.CAPACITY:
					raise Exception('invalid block capacity')
				if not block.validate_currentHash():
					raise Exception('invalid proof of work')

				if block.validate_previousHash(self.blockchain):
					# print('OK I HAVE PREVIOUS HASH')
					# start from utxos as of last block
					self.curr_utxos = copy.deepcopy(self.prev_val_utxos)
					self.wallet.transactions = []

					# print("ADD BLOCK: BLOCK LIST OF TRANSACTIONS:")
					for trans in block.listOfTransactions:
						# validate, update utxos
						# print(trans.transaction_id[:10]) 
						valid_trans = self.validate_transaction(trans)
						if not valid_trans:
							raise Exception('Validating transaction failed!')

						# remove transaction after validating
						self.wallet.transactions.remove(trans)
					# print("ADD BLOCK: BLOCK LIST OF TRANSACTIONS VALIDATED")
					# append block, update valid utxos
					self.blockchain.append(block)
					self.prev_val_utxos = copy.deepcopy(self.curr_utxos)

					# put lefto ver transactions in queue to mine next
					for trans in TRANSACTIONS_BACKUP:
						if trans not in block.listOfTransactions:
							ret = self.validate_transaction(trans)
					print("Block has been added to the chain! Block hash:", block.currentHash[:10])
					#end_time = time.time()
					#self.total_block_time += end_time - start_time
					return (True, 1)

				else:
					#CONFLICT HELP ME PLEASE
					print('--------------CONFLICT----------------')
					for ex_block in self.blockchain[:-1]:
						if ex_block.currentHash == block.previousHash:
							print("This block creates shorter chain, ignore.")
							return (False, 1)

					# time to resolve conflict
					ret = self.resolve_conflict()
					if ret == True:
						print("Block has been added to the chain! Block hash:", block.currentHash[:10])
						#end_time = time.time()
						#self.total_block_time += end_time - start_time
					return (ret, 1)

			except Exception as e:
				# restore state and return
				self.wallet.transactions = TRANSACTIONS_BACKUP
				self.blockchain = BLOCKCHAIN_BACKUP
				self.curr_utxos = UTXOS_BACKUP
				self.prev_val_utxos = VALID_UTXOS_BACKUP

				print('Block Validation fail:', e)
				return (False, 2)

	def find_longest_chain(self):
		#check for the longer chain across all nodes
		lengths = [(self.myid, len(self.blockchain))]
		network_problem = False

		for node in self.network_info:
			if node["id"] == self.myid:
				continue 
			ip = node['address'][0]
			port = node['address'][1]
			address = ip + ":" + port
			response = requests.get('{}/chain/length'.format(address))

			if response.status_code != 200:
				print(node["id"], ":", response.status_code, "Problem receiving chain length!")
				network_problem = True
				continue

			lengths.append((node["id"], response.json()['length']))

		sorted_lengths = lengths.sort(key=lambda y: y[1], reverse=True)
		max_len = sorted_lengths[0][1]
		max_length_owners = [owner[0] for owner in sorted_lengths if owner[1] == max_len]

		return (list(max_length_owners),network_problem)
	
	
	def resolve_conflict(self):
		#resolve correct chain
		with self.lock:
			BLOCKCHAIN = copy.deepcopy(self.blockchain)
			TRANSACTIONS = copy.deepcopy(self.wallet.transactions)
			UTXOS = copy.deepcopy(self.curr_utxos)
			VALID_UTXOS = copy.deepcopy(self.prev_val_utxos)
			TRANSACTIONS_BACKUP = copy.deepcopy(self.wallet.transactions)

			max_length_owners, problem = self.find_longest_chain()

			if problem:
				return False	
				
			#if my chain is already among max lengths, keep mine	
			if self.myid in max_length_owners:
				print("Kept my chain.")
				return False

			for node in self.network_info:
				if node['id'] in max_length_owners:
					ip = node['address'][0]
					port = node['address'][1]
					address = ip + ":" + port
				
					try:
						response = requests.get('{}/chain/replace'.format(address))

						if response.status_code != 200:
							print(node["id"], ":", response.status_code, "Problem receiving chain!")
							return False

						new_chain_json = response.json()['chain']
						new_chain = [Block(**json.loads(block)) for block in new_chain_json]

						for block in new_chain :
							block.listOfTransactions = [Transaction(**json.loads(t)) for t in block.listOfTransactions]
							block.nonce = str(block.nonce).encode()
							block.currentHash = str(block.currentHash).encode()
							block.previousHash = str(block.previousHash).encode()

						if not self.validate_chain(new_chain, TRANSACTIONS_BACKUP):
							raise Exception('Received invalid chain')

						#we accept first valid chain with max_len 
						#but in case of no valid chain (???) we revert to initial chain (ours)

						BLOCKCHAIN = copy.deepcopy(self.blockchain)
						TRANSACTIONS = copy.deepcopy(self.wallet.transactions)
						UTXOS = copy.deepcopy(self.curr_utxos)
						VALID_UTXOS = copy.deepcopy(self.prev_val_utxos)
						break
					except Exception as e:
						print(e)

				self.blockchain = BLOCKCHAIN
				self.transactions = TRANSACTIONS
				self.utxos = UTXOS
				self.valid_utxos = VALID_UTXOS

		return True
						




