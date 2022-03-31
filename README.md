# Distributed-Noobcash
Distributed Systems Project ECE NTUA 2022

## Description
Noobcash is a simple blockchain system for handling transactions between different nodes in a distributed network. Consensus is ensured via Proof-Of-Work.
(In-depth description (in Greek) in /docs/assignment.pdf)

## Getting Started

### Dependencies
* Ubuntu 16.04 LTS
* python3.6 and corresponding pip

### Installing
```
git clone https://github.com/aggeliki-dimitriou/distributed-noobcash
cd distributed-noobcash
pip install -r requirments.txt
```


### Executing program

* Edit config.py with your desired configuration
* Start rest
```
python3.6 rest.py [IP] [PORT]
```
* Start client (specify number of NODES if running on BOOTSTRAP mode)
```
python3.6 cli.py [IP] [PORT] [-n NODES]
```

## Help for CLI
```
Commands:
`t <RECIPIENT_ID> <AMOUNT>`         Send AMOUNT NBCs to recipient with id: RECIPIENT_ID
`view`                              View all valid transactions from the last block
`balance`                           View your own balance
`test <FILENAME>`                   Run tests in FILENAME
`stats`                             View average block time and throughput after tests
`help`                              Help message
`exit`                              Exit NOOB-CLI
```

## Authors

Angeliki Dimitriou (https://github.com/aggeliki-dimitriou)
Aphrodite Tzomaka (https://github.com/aphrodite-jomaca)
Nikodimos Marketos (https://github.com/nikodimakis)
