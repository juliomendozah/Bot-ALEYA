from pprint import pprint
import requests
import json
import sys
import sqlite3
import pandas as pd
from tabulate import tabulate
from flask import Flask
from flask import request

bearer="OTY4ZjJjMDAtMDI2Yi00ZjM3LTg3OGUtMjMzMTNiNDhkNjE1MzkxMjJiZTAtNTI1_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "Bearer " + bearer
}
database="C:/Users/julimend/OneDrive - Cisco/Para julio/CISCO ALEYA/db.sqlite3"
architectures={"collaboration":1,"data center":2,"meraki":3,"enterprise networking":4,"security":5,"small Business":6,"accesories":7,"iot":8,"industry":9,"others":10}

WEBHOOKS_LIST=["messages","memberships"]
are_webhooks=str(input("Have you create webhooks in your bot?[Yes/No]:"))
WEBHOOK_URL=str(input("What is the URL of your webhook?: "))

if are_webhooks=="Yes":
    webhooks = requests.get(url="https://webexapis.com/v1/webhooks", headers=headers)
    webhooks_data = json.loads(webhooks.text)
    webhooks_ids = []
    for webhook in webhooks_data["items"]:
        webhooks_ids.append(webhook["id"])

    for i in range(len(webhooks_ids)):
        data = {"name": "Test" + str(i), "targetUrl": WEBHOOK_URL}
        req = requests.request("PUT", "https://webexapis.com/v1/webhooks/" + webhooks_ids[i], headers=headers,
                               data=json.dumps(data))
else:
    for i in range(len(WEBHOOKS_LIST)):
        data = {"name": "TestWebhook" + str(i), "targetUrl": WEBHOOK_URL,"resource":WEBHOOKS_LIST[i],"event":"created"}
        req = requests.post("https://webexapis.com/v1/webhooks/", json.dumps(data), headers=headers).json()




def send_get(url, payload=None,js=True):

    if payload == None:
        request = requests.get(url, headers=headers)
    else:
        request = requests.get(url, headers=headers, params=payload)
    if js == True:
        request= request.json()
    return request


def send_post(url, data):

    request = requests.post(url, json.dumps(data), headers=headers).json()
    return request


def help_me():

    return "Sure! I can help. Below are the commands that I understand:<br/>" \
           "`Help me` - I will display what I can do.<br/>" \
           "`About` - I will display info about me.<br/>" \
           "`Devices` - I will show you the devices available to lend in Cisco Peru Lab. Please after Devices enter the architecture such as Collaboration, Data Center, Meraki, Enterprise Networing, Security, Small Business, Accesories, IoT,Industry, Others<br/>"


def data(architecture):
    response=""
    connection = sqlite3.connect(database)
    df = pd.read_sql_query('''SELECT id, identificador, modelo FROM Laboratorio_devices_lab WHERE ubicacion= "Almacén Lab" AND estado_id==1 AND area_id=='''+str(architectures[architecture]), connection)
    df=df.set_index("id")
    connection.close()
    response=tabulate(df, headers='keys', tablefmt='plain')
    print(response)
    return response


app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def teams_webhook():
    if request.method == 'POST':
        webhook = request.get_json(silent=True)
        if webhook['data']['personEmail']!= bot_email:
            pprint(webhook)
        if webhook['resource'] == "memberships" and webhook['data']['personEmail'] == bot_email:
            send_post("https://api.ciscospark.com/v1/messages",
                            {
                                "roomId": webhook['data']['roomId'],
                                "markdown": (greetings() +
                                             "**Note This is a group room and you have to call "
                                             "me specifically with `@%s` for me to respond**" % bot_name)
                            }
                            )
        msg = None
        if "@webex.bot" not in webhook['data']['personEmail']:
            result = send_get(
                'https://api.ciscospark.com/v1/messages/{0}'.format(webhook['data']['id']))
            in_message = result.get('text', '').lower()
            in_message = in_message.replace(bot_name.lower() + " ", '')
            if in_message.startswith('help me'):
                msg = help_me()
            elif in_message.startswith('about'):
                msg = greetings()
            elif in_message.startswith("devices"):
                message = in_message.split('devices ')[1]
                if len(message) > 0:
                    msg = data(message)
                else:
                    msg = "I did not get that. Sorry!"
            else:
                msg = "Sorry, but I did not understand your request. Type `Help me` to see what I can do"
            if msg != None:
                send_post("https://api.ciscospark.com/v1/messages",
                                {"roomId": webhook['data']['roomId'], "markdown": msg})
        return "true"
    elif request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Webex Teams Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> bot is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Webex Teams!</i></b></center>" % bot_name
        return message

def main():
    global bot_email, bot_name
    if len(bearer) != 0:
        test_auth = send_get("https://api.ciscospark.com/v1/people/me", js=False)
        if test_auth.status_code == 401:
            print("Looks like the provided access token is not correct.\n"
                  "Please review it and make sure it belongs to your bot account.\n"
                  "Do not worry if you have lost the access token. "
                  "You can always go to https://developer.webex.com/my-apps "
                  "and generate a new access token.")
            sys.exit()
        if test_auth.status_code == 200:
            test_auth = test_auth.json()
            bot_name = test_auth.get("displayName","")
            bot_email = test_auth.get("emails","")[0]
    else:
        print("'bearer' variable is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access token, view it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token for your Bot.")
        sys.exit()
    else:
        app.run(host='localhost', port=8080)
        #app.run(host='localhost', port=5000)

if __name__ == "__main__":
    main()
