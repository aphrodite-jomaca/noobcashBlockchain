import requests

import config

def broadcast(item, endpoint, nodes, myid):
    for node in nodes:
        if (node['id'] == myid):
            continue
        ip = node['address'][0]
        port = node['address'][1]
        address = ip + ":" + port
        requests.post('{}/{}'.format(address, endpoint), json=item)
    return True

def statistics(node):
    avg_block_time = node.total_block_time/len(node.blockchain)
    valid_trans = len(node.blockchain)*config.CAPACITY
    throughput = valid_trans/(node.total_trans_time - node.start_tp)
    print('Average block time:', avg_block_time, ', Throughput:', throughput)
    return avg_block_time, throughput
    
