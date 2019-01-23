# coding: UTF-8

import hashlib
import json
from textwrap import dedent
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transaction = []
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        ブロックチェーンに新しいブロックを作る
        :param proof: <int> Proof of Workアルゴリズムから得られるプルーフ
        :param prev_hash: (Option) <str> 前のブロックのハッシュ
        :return: <dictionary> 新しいブロック
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transaction,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])  # [-1] : 配列の一番うしろの要素を指定
        }

        self.current_transaction = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        次に採掘されるブロックに加える新しいトランザクションを生成する
        :param sender: <str> 送信者のアドレス
        :param recipient: <str> 受信者のアドレス
        :param amount: <int> 量
        :return: <int> このトランザクションを含むブロックのアドレス
        """
        self.current_transaction.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        })

        return self.last_block['index'] + 1

    @staticmethod  # 継承クラスでも動作が変わらないことを保証
    def hash(block):
        """
        ブロックのSHA-256ハッシュを作る
        :param block: <dictionary> ハッシュ化されるブロック
        :return: <str> ハッシュ値
        """
        # sort_keys=Trueでキーでソート．ソートされていないと一貫性の無いハッシュとなってしまう
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property  # プロパティのgetterであることを示す
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        シンプルなproof-of-workアルゴリズム
        - hash(pp')の最初の4つが0となるようなpを探す
        - pは1つ前のブロックのプルーフ，p'は新しいブロックのプルーフ
        :param last_proof: <int> p
        :return: <int> p'
        """

        proof = 0
        while self.is_valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def is_valid_proof(last_proof, crnt_proof):
        """
        hash(last_proof, current_proof)の最初の4つが0となっているかを確認
        :param last_proof: <int>
        :param crnt_proof: <int>
        :return: <bool>
        """

        guess = f'{last_proof}{crnt_proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"  # hexdigestは16進数形式文字列を返す


app = Flask(__name__)

node_id = str(uuid4()).replace('-', '')  # ランダムなユニークアドレスを生成

blockchain = Blockchain()


@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json()

    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'トランザクションはブロック{index}に追加されました'}
    return jsonify(response), 201


@app.route('/mine', methods=['GET'])
def mine():
    # 次のプルーフを見つけるためにproof of work アルゴリズムを使用する
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    blockchain.new_transaction(
        sender="0",
        recipient=node_id,
        amount=1
    )

    # チェーンに新しいブロックを加えることで，新しいブロックを採掘する
    block = blockchain.new_block(proof)

    response = {
        'message': '新しいブロックを採掘しました',
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
