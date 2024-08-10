import json
import requests
from urls import creds_file

# Load credentials from creds.json
try:
    with open(creds_file) as f:
        credentials = json.load(f)
except FileNotFoundError:
    print("Error: creds.json not found.")
    credentials = {}

# Access individual credentials
sender_phone_id = credentials.get("sender_phone_id", "")
temp_access_token = credentials.get("temp_access_token", "")

# Send message through WhatsApp Business API
def send_msg(to, message):
    url = f'https://graph.facebook.com/v15.0/{sender_phone_id}/messages'
    headers = {
        "Authorization": f"Bearer {temp_access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        pass
    else:
        print("Failed to send message. Error:", response.text)


def send_btn_msg(to, message, raw_btn_list, btn_ids_list=[]):
    url = f'https://graph.facebook.com/v15.0/{sender_phone_id}/messages'
    headers = {
        "Authorization": f"Bearer {temp_access_token}",
        "Content-Type": "application/json"
    }
    refined_btn_list = []
    for i, btn in enumerate(raw_btn_list):
        if btn_ids_list != []:
            refined_btn_list.append({"type": "reply", "reply": {'id': btn_ids_list[i], 'title': btn}})
        else:
            refined_btn_list.append({"type": "reply", "reply": {'id': f'btn_id_{i + 1}', 'title': btn}})
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": message
            },
            "action": {
                "buttons": refined_btn_list
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        pass
    else:
        print("Failed to send message. Error:", response.text)