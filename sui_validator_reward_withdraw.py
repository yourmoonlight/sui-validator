import sys
import json
import time
import requests
from requests.exceptions import RequestException
import subprocess


url = "https://fullnode.testnet.sui.io/" # or https://fullnode.mainnet.sui.io/
gas_budget = 20000000
recipient_addr = "xxx"

def req_rpc_getOwnedObjects(struct_type):
    payload = json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "suix_getOwnedObjects",
    "params": [
        "xxx", #validator addr
        {
        "filter": {
            "MatchAll": [
            {
                "StructType": struct_type
            },
            {
                "AddressOwner": "xxx" #validator addr
            }
            ]
        },
        "options": {
            "showType": True,
            "showOwner": True,
            "showPreviousTransaction": False,
            "showContent": True,
            "showDisplay": False,
            "showBcs": False,
            "showStorageRebate": False
        }
        }
    ]
    })
    headers = {
    'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        j = json.loads(response.text)
        data = j["result"]["data"]
        return data
    except RequestException as err:
        print(f"request req_rpc_getOwnedObjects got some request error: {err}")
    except Exception as err:
        print(f"request req_rpc_getOwnedObjects got other err:{err}")

def withdraw_stake_reward():
    data = req_rpc_getOwnedObjects("0x3::staking_pool::StakedSui")
    to_withdraw_objectIds = [i["data"]["objectId"] for i in data]
    for staked_object_id in to_withdraw_objectIds:
        print(f">> request_withdraw_stake for stake_obj_id: {staked_object_id}")
        # call the request_withdraw_stake
        ret = subprocess.call(f'sui client call --package 0x3 --module sui_system --function request_withdraw_stake --args 0x5 {staked_object_id} --gas-budget {gas_budget}', shell=True)
        if ret != 0 :
            print(f"call the request_withdraw_stake got error, staked_object_id: {staked_object_id}")
            sys.exit(1)
        time.sleep(5)

def mergin_coin():
    data = req_rpc_getOwnedObjects("0x2::coin::Coin<0x2::sui::SUI>")
    if len(data) < 3:
        print("wait at least 3 coins to start merge")
        return
    to_merge_objectIds = [i["data"]["objectId"] for i in data][:-1]
    print(f">> mergin_coin to_merge_objectIds: {to_merge_objectIds}")
    primary_coin = to_merge_objectIds[0]
    print(f">> primary_coin: {primary_coin}")
    for coin_to_merge in to_merge_objectIds[1:]:
        print(f">> coin_to_merge: {coin_to_merge}")
        ret = subprocess.call(f"sui client merge-coin --primary-coin {primary_coin} --coin-to-merge  {coin_to_merge} --gas-budget {gas_budget}", shell=True)
        if ret != 0 :
            print(f"Failed to merge-coin primary_coin:{primary_coin} coin_to_merge:{coin_to_merge}")
        time.sleep(10)

def transfer():
    # get to transfer coin balance
    data = req_rpc_getOwnedObjects("0x2::coin::Coin<0x2::sui::SUI>")
    coin_balance = int(data[0]["data"]["content"]["fields"]['balance'])
    sui_coin_object_id = data[0]["data"]["objectId"]

    # call the transfer-sui
    if coin_balance < gas_budget*100:
        print(f"coin_balance too small, now is: {coin_balance}")
        return

    to_send_amount = round((coin_balance-100*gas_budget))
    print(f">> transfer-sui amount:{to_send_amount} recipient_addr:{recipient_addr}")


    ret = subprocess.call(f"sui client transfer-sui --amount {to_send_amount} --gas-budget {gas_budget} --sui-coin-object-id {sui_coin_object_id} --to {recipient_addr}", shell=True)
    if ret != 0 :
        print(f"Failed to transfer-sui amount:{to_send_amount} recipient_addr:{recipient_addr}")

def loop():
    while True:
        print(f"start the withdraw daily loop")
        withdraw_stake_reward()
        mergin_coin()
        transfer()
        time.sleep(24 * 60 * 60)

if __name__ == "__main__":
    loop()