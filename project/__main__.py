from pyngrok import ngrok
from project.webhook_listener import start_main
import json
import subprocess

ngrok.set_auth_token("2H2oJnPcjCcTXMd92NLMtRIQwsl_66t2W3QLNi24AAT2gKS3y")
tunnel_connection: ngrok.NgrokTunnel = ngrok.connect(proto='http', addr=5000, bind_tls=True)

with open('.\\data\\users.json', "r", encoding='utf-8') as file:
    data = json.load(file)

users = list(data.keys())
print("= Which user are you? =\n0. Add a new user")
for i, user in enumerate(users):
    print(f"{i+1}. {user}")
selected_user = input()
if int(selected_user) > 0:
    telegram_active = False
    tl_id = users[int(selected_user)-1]
else:
    print("= Starting Telegram bot, please authenticate using /start!")

    # EDIT HERE for different environment!
    telegram = subprocess.Popen(['powershell.exe', '-Command',
                                 f"{__file__[:-19]}\\venv\\Scripts\\activate.ps1 ; python -m project.telegram_bot"],
                                cwd=__file__[:-19], creationflags=subprocess.CREATE_NEW_CONSOLE)
    telegram_active = True
    input("Did the user AUTHENTICATE with the Telegrambot? [ANY KEY TO CONTINUE]")
    tl_id = input("What is the telegramID?")
    print(tl_id)

url = tunnel_connection.public_url+'/tripper'
print(f"Webhook listener on {url}")
start_main(tl_id, url)
if telegram_active:
    telegram.terminate()
print('Tripper has stopped')
