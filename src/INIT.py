import os,sys,json,glob, traceback
from client.contractnote import ContractNote
from client.bcosclient import BcosClient
from client.datatype_parser import DatatypeParser
from client.common.compiler import Compiler
from client.bcoserror import BcosException, BcosError
from client_config import client_config
from eth_utils import to_checksum_address
from eth_utils.hexadecimal import encode_hex
from eth_account.account import Account
from phe import paillier
import pickle

# 从文件加载abi定义
if os.path.isfile(client_config.solc_path) or os.path.isfile(client_config.solcjs_path):
    Compiler.compile_file("contracts/platform.sol")
abi_file = "contracts/platform.abi"
data_parser = DatatypeParser()
data_parser.load_abi_file(abi_file)
contract_abi = data_parser.contract_abi

try:
    client = BcosClient()
    print(client.getinfo())
    # 部署合约
    print("\n>>Deploy:----------------------------------------------------------")
    with open("contracts/platform.bin", 'r') as load_f:
        contract_bin = load_f.read()
        load_f.close()
    result = client.deploy(contract_bin)
    print("deploy", result)
    print("new address : ", result["contractAddress"])
    contract_name = os.path.splitext(os.path.basename(abi_file))[0]
    memo = "tx:" + result["transactionHash"]
    # 把部署结果存入文件备查
    ContractNote.save_address_to_contract_note(contract_name,
                                               result["contractAddress"])
    # 创建表格
    to_address = result['contractAddress'] 
    receipt = client.sendRawTransactionGetReceipt(to_address,contract_abi,"create_company_table")
    if receipt['output'] != 0:
        print("company_table already exists.")
    else: 
        print("create company_table successfully.")
    receipt = client.sendRawTransactionGetReceipt(to_address,contract_abi,"create_receipt_table")
    if receipt['output'] != 0:
        print("receipt_table already exists.")
    else: 
        print("create receipt_table successfully.")
        
except BcosException as e:
    print("execute demo_transaction failed ,BcosException for: {}".format(e))
    traceback.print_exc()
except BcosError as e:
    print("execute demo_transaction failed ,BcosError for: {}".format(e))
    traceback.print_exc()
except Exception as e:
    client.finish()
    traceback.print_exc()
client.finish()

# 获取同态加密公私钥对
public_key, private_key = paillier.generate_paillier_keypair(n_length=64)
if (not os.path.isfile("PaillierPublicKey.pkl")) or (not os.path.isfile("PaillierPrivateKey.pkl")):
    with open("PaillierPublicKey.pkl", 'wb') as f:
        str = pickle.dumps(public_key)
        f.write(str)
    with open("PaillierPrivateKey.pkl", 'wb') as f:
        str = pickle.dumps(private_key)
        f.write(str)
sys.exit(0)