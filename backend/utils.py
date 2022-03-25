import requests
import json

def broadcast(item, endpoint, nodes, myid):
    for node in nodes:
        if (node['id'] == myid):
            continue
        ip = node['address'][0]
        port = node['address'][1]
        address = ip + ":" + port
        response = requests.post('{}/{}'.format(address, endpoint), json=json.dumps(item))
    return True
    
