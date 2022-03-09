import binascii

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4



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
		for utxo in node.utxos[self.public_key]: 
			balance+=utxo['amount']
		return balance 

