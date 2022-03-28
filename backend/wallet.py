
import Crypto.Random
from Crypto.PublicKey import RSA

class Wallet:

	def __init__(self,address):
		##set
		self.generate_wallet()
		self.address = address
		self.transactions = []

	def generate_wallet(self):
		randfunc = Crypto.Random.new().read 
		self.private_key  = RSA.generate(2048,randfunc)
		self.public_key = self.private_key.publickey().exportKey().decode()

	def wallet_balance(self, node):
		balance = 0
		for utxo in node.curr_utxos[self.public_key]: 
			balance+=utxo['amount']
		return balance 

