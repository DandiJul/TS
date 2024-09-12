import asyncio
import websockets
import json
import os
import sys
import time

async def connect_websocket(account_data, account_number, total_accounts):
    uri = "wss://app.tomato.fun/game"
    
    payload_init = {
        "cmd": "init",
        "msg": account_data
    }
    payload_get_tasks = {
        "cmd": "get_tasks"
    }
    payload_tap = {
        "cmd": "tap"
    }
    payload_claim = {
        "cmd": "claim"
    }

    try:
        async with websockets.connect(uri) as websocket:
            print(f"[INFO] Memproses Akun {account_number}/{total_accounts}")

            tap_count = 0

            while True:
                await websocket.send(json.dumps(payload_init))

                response = await websocket.recv()
                data = json.loads(response)
                if isinstance(data, list) and data[0] == "init_response":
                    user_data = data[1]

                    await websocket.send(json.dumps(payload_get_tasks))

                    response = await websocket.recv()
                    data = json.loads(response)
                    if isinstance(data, list) and data[0] == "get_tasks_response":

                        while tap_count < 10:
                            await websocket.send(json.dumps(payload_tap))

                            response = await websocket.recv()
                            data = json.loads(response)
                            if isinstance(data, dict) and 'temp_balance' in data:
                                user_data['temp_balance'] = data['temp_balance']

                            tap_count += 1
                            await asyncio.sleep(3)

                            if user_data['temp_balance'] >= 500:
                                await websocket.send(json.dumps(payload_claim))

                                response = await websocket.recv()
                                claim_data = json.loads(response)

                                if isinstance(claim_data, list) and claim_data[0] == "claim_response" and claim_data[1]["ok"]:
                                    updated_balance = claim_data[1]["updated_balance"]
                                    recovery_time = claim_data[1]["recovery_time"]

                                    wait_time = recovery_time - int(time.time())
                                    if wait_time > 0:
                                        while wait_time > 0:
                                            sys.stdout.flush()
                                            await asyncio.sleep(1)
                                            wait_time -= 1

                                break

                        print(f"{user_data['username']:20} | Tap Balance: {user_data['temp_balance']:6} | Claimed: {user_data['claimed']:6} | Balance: {user_data['balance']:8}")
                        await asyncio.sleep(5)
                        os.execv(sys.executable, ['python3'] + sys.argv)

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"{account_data:20} | Error: Connection closed")
    except Exception as e:
        print(f"{account_data:20} | Error: {e}")

async def main():
    with open("akun.txt", "r") as file:
        accounts = file.readlines()

    total_accounts = len(accounts)
    print(f"[INFO] Total Akun: {total_accounts}")

    tasks = []
    for i, account_data in enumerate(accounts, start=1):
        account_data = account_data.strip()
        tasks.append(connect_websocket(account_data, i, total_accounts))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except AttributeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
