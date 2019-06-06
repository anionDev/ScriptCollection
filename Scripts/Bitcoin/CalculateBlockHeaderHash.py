import argparse
import hashlib 
import binascii
parser = argparse.ArgumentParser(description='Calculates the Hash of the header of a bitcoin-block.')

parser.add_argument('--version', help='Block-version')
parser.add_argument('--previousblockhash', help='TODO')
parser.add_argument('--transactionsmerkleroot', help='Hashvalue of the transactions which are contained in the block')
parser.add_argument('--timestamp', help='Timestamp of the block')
parser.add_argument('--target', help='difficulty')
parser.add_argument('--nonce', help='Arbitrary 32-bit-integer-value')

args = parser.parse_args()

header = str(args.version + args.previousblockhash + args.transactionsmerkleroot + args.timestamp + args.target + args.nonce)
print(binascii.hexlify(hashlib.sha256(hashlib.sha256(binascii.unhexlify(header)).digest()).digest()[::-1]).decode('utf-8'))