# from collections import OrderedDict

# import binascii

# import Crypto
import Crypto.Random
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
import base64
import json

# import requests
# from flask import Flask, jsonify, request, render_template


class Transaction:

    def __init__(self, sender_address, recipient_address, amount, transaction_inputs):

        ##set

        #self.timestamp = time()
        self.sender_address = sender_address # To public key του wallet από το οποίο προέρχονται τα χρήματα
        self.recipient_address = recipient_address  # To public key του wallet στο οποίο θα καταλήξουν τα χρήματα
        self.amount = amount # το ποσό που θα μεταφερθεί
        self.transaction_id = None # το hash του transaction
        self.transaction_inputs = transaction_inputs  # λίστα από Transaction Input 
        self.transaction_outputs = []    # λίστα από Transaction Output 
        self.signature = None

    

    def to_json(self):
        return json.dumps(self.__dict__)

    def create_transaction_id(self):
         self.transaction_id = str(SHA256.new(self.to_json().encode()).hexdigest())

    def sign_transaction(self, priv_key):
        """
        Sign transaction with private key
        """
        object_hash = SHA256.new(data = self.transaction_id.encode())
        signer = PKCS1_v1_5.new(priv_key)
        self.signature = base64.b64encode(signer.sign(object_hash))
       
    def verify_signature(self):
        pub_rsa = RSA.importKey(self.sender_address.encode())
        verifier = PKCS1_v1_5.new(pub_rsa)
        objest_hash = SHA256.new(data = self.transaction_id.encode())
        return verifier.verify(objest_hash, base64.b64decode(self.signature))

    
