import json
from db import get_events_by_key_name, establish_connection
from constants import Protocol, get_symbol

conn = establish_connection()
borrowing = get_events_by_key_name(Protocol.ZKLEND, "Borrowing", conn)
repayment = get_events_by_key_name(Protocol.ZKLEND, "Repayment", conn)
liquidation = get_events_by_key_name(Protocol.ZKLEND, "Liquidation", conn)
conn.close()

state = {}

for event in borrowing:
    data = event['data']
    user = data[0]
    token = get_symbol(data[1])
    raw_amount = int(data[2], base=16)
    user_token = "{}:{}".format(user,token)
    if user_token in state:
        state[user_token] += raw_amount
    else:
        state[user_token] = raw_amount

for event in repayment:
    data = event['data']
    user = data[1]
    token = get_symbol(data[2])
    raw_amount = int(data[3], base=16)
    user_token = "{}:{}".format(user,token)
    if user_token in state:
        state[user_token] -= raw_amount
    else:
        state[user_token] = raw_amount

for event in liquidation:
    data = event['data']
    user = data[1]
    token = get_symbol(data[2])
    raw_amount = int(data[3], base=16)
    user_token = "{}:{}".format(user,token)
    if user_token in state:
        state[user_token] -= raw_amount
    else:
        state[user_token] = raw_amount

with open("state.json", "w") as outfile:
    outfile.write(json.dumps(state, indent=4))
