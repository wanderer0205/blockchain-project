import os, sys, json, traceback, pickle
from client.contractnote import ContractNote
from client.bcosclient import BcosClient
from eth_utils import to_checksum_address
from eth_utils.hexadecimal import encode_hex
from client.datatype_parser import DatatypeParser
from client.common.compiler import Compiler
from client.bcoserror import BcosException, BcosError
from client_config import client_config
from eth_account.account import Account
from phe import paillier

class tempClient():
    """
    注册企业用的client
    """
    def __init__(self):
        self.client = BcosClient()
        self.to_address = None
        self.contract_abi = None
        self.isOK = False
        try:
            abi_file = "contracts/platform.abi"
            data_parser = DatatypeParser()
            data_parser.load_abi_file(abi_file)
            self.contract_abi = data_parser.contract_abi
            self.to_address = ContractNote.get_last("platform")
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return
        except Exception as e:
            traceback.print_exc()
            return
        # 同态加密
        self.homo_PublicKey = None
        self.homo_PrivateKey = None
        try:
            with open("PaillierPublicKey.pkl",'rb') as file:
                self.homo_PublicKey = pickle.loads(file.read())
            with open("PaillierPrivateKey.pkl",'rb') as file:
                self.homo_PrivateKey = pickle.loads(file.read())
        except:
            print("load homomorphic key file error!")
            return
        self.isOK=True

    def register(self, name, level, credit, address):
        """
        注册相关企业
        """
        args = [ name, 
                 int(level), 
                 str(self.homo_PublicKey.encrypt(int(credit)).ciphertext()), 
                 to_checksum_address(address) ]
        try:
            res = self.client.call(self.to_address, self.contract_abi,"register",args)
            if res[0] != -1:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi,"register",args)
                print("receipt:",receipt['output'])
            else:
                return -2
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return 0

class myClient():
    """
    正式client
    """
    def __init__(self, name=None, password=None):
        keyfile = "{}/{}.keystore".format(client_config.account_keyfile_path, name)
        # 如果账户不存在
        if os.path.exists(keyfile) is False:
            print("No such User! ")
            self.isOK=False
            return
        else:
            print("name : {}, keyfile:{} ,password {}  ".format(name, keyfile, password))
            try:
                with open(keyfile, "r") as dump_f:
                    keytext = json.load(dump_f)
                    private_key = Account.decrypt(keytext, password)
                    tempAccount = Account().from_key(private_key)
                    print("address:\t", tempAccount.address)
                    print("private_key:\t", encode_hex(tempAccount.privateKey))
                    print("public_key :\t", tempAccount.publickey)
            except Exception as e:
                print(e)
                self.isOK=False
                return
        self.account_name = name
        self.account_address = tempAccount.address.lower()
        self.account_public_key = tempAccount.publickey
        self.account_private_key = tempAccount.privateKey
        self.account_status = None
        self.account_level = None
        self.account_credit = None
        self.to_address = None
        self.contract_abi = None
        self.client = BcosClient()
        # 同态加密
        self.homo_PublicKey = None
        self.homo_PrivateKey = None
        try:
            with open("PaillierPublicKey.pkl",'rb') as file:
                self.homo_PublicKey = pickle.loads(file.read())
            with open("PaillierPrivateKey.pkl",'rb') as file:
                self.homo_PrivateKey = pickle.loads(file.read())
        except:
            print("load homomorphic key file error!")
            self.isOK=False
            return

        self.renew_contract_data()
        self.renew_account_data()
        self.isOK=True

    def finish(self):
        self.account_name = None
        self.account_address = None
        self.account_public_key = None
        self.account_private_key = None
        self.account_status = None
        self.account_level = None
        self.account_credit = None
        self.to_address = None
        self.contract_abi = None
        self.homo_PublicKey = None
        self.homo_PrivateKey = None
        self.isOK = False
        self.client.finish()

    def renew_contract_data(self):
        """
        更新合约相关参数
        """
        try:
            abi_file = "contracts/platform.abi"
            data_parser = DatatypeParser()
            data_parser.load_abi_file(abi_file)
            self.contract_abi = data_parser.contract_abi
            self.to_address = ContractNote.get_last("platform")
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
        except Exception as e:
            traceback.print_exc()

    def renew_account_data(self):
        """
        更新账户相关参数
        """
        try:
            result = self.client.call(self.to_address, self.contract_abi, "select_company")
            num = len(result[0])
            for i in range(num):
                if result[0][i]==self.account_name and result[1][i].lower()==self.account_address.lower():
                    self.account_status = result[2][i]
                    self.account_level = result[3][i]
                    self.account_credit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[4][i])))
                    break
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
        except Exception as e:
            traceback.print_exc()

    def getFromReceipt(self, name=None):
        """
        查询债务人为name的单据
        """
        condition = [name, 0]
        mess = list()
        if name is None:
            condition[0] = self.account_name
        try:
            result = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byCompany", condition)
            num = len(result[0])
            for i in range(num):
                mess.append({'id': result[0][i], 
                             'from': condition[0], 
                             'to': result[1][i], 
                             'cur_bill': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[2][i]))),
                             'ori_bill': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[3][i]))),
                             'status': result[4][i],
                             'due': result[5][i]})
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return None
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return None
        except Exception as e:
            traceback.print_exc()
            return None
        if len(mess)>0:
            mess=sorted(mess, key = lambda i: i['id'])
        return mess

    def getToReceipt(self, name=None):
        """
        查询债权人为name的单据
        """
        condition = [name, 1]
        mess = list()
        if name is None:
            condition[0] = self.account_name
        try:
            result = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byCompany", condition)
            num = len(result[0])
            for i in range(num):
                mess.append({'id': result[0][i], 
                             'from': result[1][i], 
                             'to': condition[0],
                             'cur_bill': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[2][i]))),
                             'ori_bill': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[3][i]))),
                             'status': result[4][i],
                             'due': result[5][i]})
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return None
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return None
        except Exception as e:
            traceback.print_exc()
            return None
        if len(mess)>0:
            mess=sorted(mess, key = lambda i: i['id'])
        return mess

    def getAllReceipts(self):
        """
        查询全部单据
        """
        try:
            print(self.to_address)
            result2 = self.client.call(self.to_address, self.contract_abi, "select_company")
            mess = list()
            for name in result2[0]:
                condition = [name, 1]
                result = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byCompany", condition)
                num=len(result[0])
                for i in range(num):
                    mess.append({'id': result[0][i], 
                                 'from': result[1][i], 
                                 'to': condition[0], 
                                 'cur_bill': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[2][i]))),
                                 'ori_bill': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[3][i]))),
                                 'status': result[4][i],
                                 'due': result[5][i]})
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return None
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return None
        except Exception as e:
            traceback.print_exc()
            return None
        if len(mess)>0:
            mess=sorted(mess, key = lambda i: i['id'])
        return mess

    def getAllCompany(self):
        """
        查询全部企业
        """
        try:
            result = self.client.call(self.to_address, self.contract_abi, "select_company")
            mess = list()
            num = len(result[0])
            for i in range(num):
                mess.append({'name': result[0][i],
                             'address': result[1][i],
                             'status': result[2][i],
                             'level': result[3][i],
                             'credit': self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(result[4][i]))) 
                             })
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return None
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return None
        except Exception as e:
            traceback.print_exc()
            return None
        return mess

    def purchase(self, To, bill, date):
        """
        发起交易，签订单据
        """
        try:
            self.renew_account_data()
            if int(bill)>self.account_credit:
                return -2
            args=[ self.account_name, 
                   To, 
                   str(self.homo_PublicKey.encrypt(int(bill)).ciphertext()),
                   date, 
                   to_checksum_address(self.account_address)]
            res = self.client.call(self.to_address, self.contract_abi, "purchase", args)
            if res[0]==0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "purchase", args)
                print(receipt)
            return res[0]
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1

    def verify(self, Id, choice):
        """
        验证交易
        """
        try:
            args=[int(Id), int(choice), to_checksum_address(self.account_address)]
            res = self.client.call(self.to_address, self.contract_abi, "verify_trade", args)
            if res[0]>0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "verify_trade", args)
                print(receipt)
                if int(choice)==1:
                    # 修改双方信用
                    args=[int(Id)]
                    res = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byID", args)
                    ecredit = int(res[2][0])
                    credit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, ecredit))
                    From = res[0][0]
                    To = res[1][0]
                    
                    args=[From]
                    res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                    FromCredit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                    args=[To]
                    res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                    ToECredit = int(res[3][0])
                    args=[
                        From,
                        To,
                        str(self.homo_PublicKey.encrypt(FromCredit-credit).ciphertext()), 
                        str(ecredit*ToECredit)
                    ]
                    receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "renew_credit", args)
                    print(receipt)
                return 0
            else: 
                return -1
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1

    def revoke(self, Id):
        """
        撤销交易
        """
        try:
            args=[int(Id), to_checksum_address(self.account_address)]
            res = self.client.call(self.to_address, self.contract_abi, "revoke_receipt", args)
            if res[0]==0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "revoke_receipt", args)
                print(receipt)
                # 获取交易内容
                args=[int(Id)]
                res = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byID", args)
                cur = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[2][0])))
                ori = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                left = ori-cur
                From = res[0][0]
                To = res[1][0]
                due = res[5][0]
                # 恢复信用
                args=[From]
                res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                FromCredit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                args=[To]
                res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                ToCredit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                args=[ To, From,
                       str(self.homo_PublicKey.encrypt(ToCredit-left).ciphertext()), 
                       str(self.homo_PublicKey.encrypt(FromCredit+left).ciphertext()) ]
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "renew_credit", args)
                print(receipt)
                if left>0:
                    args = [ To, From,
                             str(self.homo_PublicKey.encrypt(left).ciphertext()),
                             1, due ]
                    receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "insert_receipt", args)
                print(receipt)
                return 0
            else: 
                return -1
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1

    def transfer(self, Id, To, Sum):
        """
        转让单据
        """
        try:
            # 获取交易内容
            Sum=int(Sum)
            args=[int(Id)]
            res = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byID", args)
            OriTo = res[1][0]
            cur = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[2][0])))

            update_status=1
            left=cur-Sum
            if left<0:
                return -2
            elif left==0:
                update_status=2
            args = [int(Id), To, 
                    str(self.homo_PublicKey.encrypt(left).ciphertext()), 
                    str(self.homo_PublicKey.encrypt(Sum).ciphertext()), 
                    update_status, 
                    to_checksum_address(self.account_address)]
            res = self.client.call(self.to_address, self.contract_abi, "transfer", args)
            if res[0]==0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "transfer", args)
                print(receipt)
                # 修改双方信用
                args=[OriTo]
                res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                OriToCredit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                args=[To]
                res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                ToCredit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                args=[
                    OriTo,
                    To,
                    str(self.homo_PublicKey.encrypt(OriToCredit-Sum).ciphertext()), 
                    str(self.homo_PublicKey.encrypt(ToCredit+Sum).ciphertext())
                ]
                res = self.client.call(self.to_address, self.contract_abi, "renew_credit", args)
                if res[0]==0:
                    receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "renew_credit", args)
                    print(receipt)
                else:
                    return -1
                return 0
            else: 
                return -1
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1

    def finance(self, Id, To, Sum):
        """
        融资
        """
        return self.transfer(Id, To, Sum)

    def repay(self, Id, Sum):
        """
        偿还
        """
        try:
            # 获取交易内容
            args=[int(Id)]
            res = self.client.call(self.to_address, self.contract_abi, "select_Receipt_byID", args)
            cur = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[2][0])))

            if cur<=int(Sum):
                new_status=2
            else:
                new_status=1
            args = [ int(Id), 
                     str(self.homo_PublicKey.encrypt(cur-int(Sum)).ciphertext()), 
                     new_status, 
                     to_checksum_address(self.account_address) ]
            res = self.client.call(self.to_address, self.contract_abi, "repay", args)
            if res[0]==0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "repay", args)
                print(receipt)

                args = [self.account_name]
                res = self.client.call(self.to_address, self.contract_abi, "select_company_byName", args)
                credit = self.homo_PrivateKey.decrypt(paillier.EncryptedNumber(self.homo_PublicKey, int(res[3][0])))
                self.update_company(self.account_name, res[0][0], res[1][0], res[2][0], credit+int(Sum))
                return 0
            else: 
                return -1
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1

    def update_company(self, name, address, status, level, credit):
        try:
            args=[name, to_checksum_address(address), int(status), int(level), str(self.homo_PublicKey.encrypt(int(credit)).ciphertext())]
            res = self.client.call(self.to_address, self.contract_abi, "update_company", args)
            if res[0]>0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "update_company", args)
                print(receipt)
                return 0
            else: 
                return -1
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1

    def broke(self):
        try:
            args=[self.account_name, to_checksum_address(self.account_address)]
            res = self.client.call(self.to_address, self.contract_abi, "set_bankrupt", args)
            print(res)
            if res[0]>=0:
                receipt = self.client.sendRawTransactionGetReceipt(self.to_address, self.contract_abi, "set_bankrupt", args)
                print(receipt)
                return 0
            else: 
                return -1
        except BcosException as e:
            print("execute demo_transaction failed ,BcosException for: {}".format(e))
            traceback.print_exc()
            return -1
        except BcosError as e:
            print("execute demo_transaction failed ,BcosError for: {}".format(e))
            traceback.print_exc()
            return -1
        except Exception as e:
            traceback.print_exc()
            return -1
        return -1


