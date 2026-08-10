import json
import requests
from config import TITLE_ID, SECRET_KEY

URL = "https://" + TITLE_ID + ".playfabapi.com"

ME = {"ticket": "", "id": "", "nome": ""}

def api(caminho, dados, admin=False):
    if admin == True:
        cabecalhos = {"X-SecretKey": SECRET_KEY}
    else:
        cabecalhos = {"X-Authorization": ME["ticket"]}
        
    resposta = requests.post(URL + caminho, json=dados, headers=cabecalhos).json()
    
    if "data" not in resposta:
        raise Exception(resposta.get("errorMessage", str(resposta)))
        
    return resposta["data"]

def ler(chave, padrao=None):
    dados = api("/Admin/GetTitleData", {"Keys": [chave]}, admin=True)["Data"]
    if chave in dados:
        return json.loads(dados[chave])
    return padrao

def gravar(chave, valor):
    api("/Admin/SetTitleData", {"Key": chave, "Value": json.dumps(valor)}, admin=True)

def ler_user(playfab_id, chave, padrao=None):
    dados = api("/Server/GetUserData", {"PlayFabId": playfab_id, "Keys": [chave]}, admin=True)["Data"]
    if chave in dados:
        return float(dados[chave]["Value"])
    return padrao

def gravar_user(playfab_id, chave, valor):
    api("/Server/UpdateUserData", {"PlayFabId": playfab_id, "Data": {chave: str(valor)}}, admin=True)
