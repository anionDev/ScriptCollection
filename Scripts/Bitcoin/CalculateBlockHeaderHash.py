import argparse
from hashlib import sha256
import hashlib 

parser = argparse.ArgumentParser(description='Calculates the Hash of the header of a bitcoin-block.')

parser.add_argument('version', help='TODO')
parser.add_argument('previousblockhash', help='TODO')
parser.add_argument('transactionsmerkleroot', help='TODO')
parser.add_argument('timestamp', help='TODO')
parser.add_argument('target', help='TODO')
parser.add_argument('nonce', help='TODO')

args = parser.parse_args()
#TODO: do something like
#header = str(args.version + args.previousblockhash + args.transactionsmerkleroot + args.timestamp + args.target + args.nonce)
#print(sha256(sha256(header).digest()).digest()[::-1].encode('hex'))