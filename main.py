import os
import requests
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
import dotenv
from flask import Flask, redirect, request, url_for, jsonify
from icalendar import Calendar, Event
import caldav
from datetime import datetime
from datetime import timedelta
import time
import pytz
import json

# Charger les variables d'environnement à partir du fichier .env
if os.path.exists('.env'):
    dotenv.load_dotenv()
elif os.getenv('UID') == "":
    with open('.env', 'w') as f:
        f.write('UID=\"'+input("UID API 42 : ")+'\"\nSECRET=\"'+input("SECRET API 42 : ")+'\"\nTOKEN=\"\"\nADDRESS=\"'+input("SERVER ADDRESS : ")+'\"'+'LOGIN=\"'+input("42 LOGIN : ")+'\"')

# Récupérer les identifiants client
UID = os.getenv('UID')
SECRET = os.getenv('SECRET')
token = os.getenv('TOKEN')
ADDRESS = os.getenv('ADDRESS')
LOGIN = os.getenv('LOGIN')
DAVICAL_URL = os.getenv('DAVICAL_URL')
DAVICAL_USER = os.getenv('DAVICAL_USER')
DAVICAL_PASS = os.getenv('DAVICAL_PASS')

# URL pour obtenir le jeton d'accès et d'autorisation
authorization_base_url = 'https://api.intra.42.fr/oauth/authorize'
token_url = 'https://api.intra.42.fr/oauth/token'

# Scopes requis
scopes = ['public', 'profile', 'projects']

# Créer un client OAuth2 avec les scopes
client = WebApplicationClient(client_id=UID)
oauth = OAuth2Session(client=client, scope=scopes, redirect_uri='http://'+ADDRESS+'/callback')

loged = False

app = Flask(__name__)

api_url = 'https://api.intra.42.fr/v2/slots'
headers = {
    'Authorization': f'Bearer {token}'
}
try:
    response = requests.get(api_url, headers=headers)
    print(response.json())
    print(response.status_code)
    if response.status_code == 200:
        loged = True
    else:
        loged = False
        print('Erreur: Impossible de se connecter à l\'API avec le token fournis , veuillez ouvrir le lien suivant pour obtenir un nouveau token')
        print('http://'+ADDRESS+'/')
except Exception as e:
    print(e)


@app.route('/')
def index():
    if loged == False:
        # Rediriger l'utilisateur vers la page d'autorisation
        authorization_url, state = oauth.authorization_url(authorization_base_url)
        return redirect(authorization_url)
    else:
        return 'Vous êtes connecté'

@app.route('/callback')
def callback():
    # Obtenir le code d'autorisation de la requête
    code = request.args.get('code')
    
    if not code:
        print('Erreur: Aucun code d\'autorisation reçu') 
        return 'Erreur: Aucun code d\'autorisation reçu', 400
    
    # Préparer les données pour la requête POST
    data = {
        'grant_type': 'authorization_code',
        'client_id': UID,
        'client_secret': SECRET,
        'code': code,
        'redirect_uri': 'http://'+ADDRESS+'/callback'
    }
    
    # Effectuer la requête POST pour obtenir le jeton d'accès
    response = requests.post(token_url, data=data)
    token = response.json()
    
    if 'error' in token:
        print(f"Erreur: {token['error_description']}")
        return f"Erreur: {token['error_description']}", 400
    
    # Extraire le jeton d'accès
    try:
        access_token = token['access_token']
        dotenv.set_key(dotenv_path=".env", key_to_set="TOKEN", value_to_set=access_token)
        token = access_token
        print('Token d\'accès obtenu avec succès et enregistré dans le fichier .env')
    except KeyError:
        print('Erreur: Impossible de récupérer le jeton d\'accès')
        print(token)
        return redirect(url_for('index'))
    
    # Utiliser le jeton d'accès pour faire une requête à l'API
    api_url = 'https://api.intra.42.fr/v2/me/scale_teams'
    global headers
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(api_url, headers=headers)
    print(response.json())

    # Afficher la réponse de l'API
    return response.json()


### Recuperer toutes les 2 minutes les slots de l'API 42, si un evennement est deja enregistré sur le serveur Davical et qu'il est modifié (champ correcteds),
### recherche l'utilisateur via une requette sur /v2/users/{id} et met a jour l'evennement sur le serveur Davical en ajoutant les données des champs displayname et location

@app.route('/update')
def update():
    # Obtenir les données de l'API 42
    api_url = 'https://api.intra.42.fr/v2/me/scale_teams'
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        loged = False
        return f'Erreur: Impossible de récupérer les données de l\'API 42: {response.content}', response.status_code
    else:
        data = response.json()
        clienDaviCal = caldav.DAVClient(url=DAVICAL_URL, username=DAVICAL_USER, password=DAVICAL_PASS)
        principal = clienDaviCal.principal()
        calendars = principal.calendars()

        if not calendars:
            print('Erreur: Aucun calendrier trouvé sur le serveur Davical')
            return 'Erreur: Aucun calendrier trouvé sur le serveur Davical', 500

        calendar = calendars[0]
        # Récupérer les événements existants
        existing_events = calendar.events()
        existing_event_uids = {event.vobject_instance.vevent.uid.value: event for event in existing_events}

        
        # Créer un objet Calendar
        if len(data) != 0:
            cal = Calendar()
            for item in data:
                event_uid = item['id']
                if type(item["correcteds"]) != str:
                    for j in range(len(item["correcteds"])):
                        print(item["correcteds"][j])
                        if item["correcteds"][j]["login"] == LOGIN:
                            EventString = "Peer-Evaluation par :"
                            if type(item["corrector"]) != str:
                                Correcteur = item["corrector"]["login"]
                                CorrecteurLoc = requests.get(f'https://api.intra.42.fr/v2/users/{Correcteur}', headers=headers).json()["location"]
                            else:
                                Correcteur = "A venir"
                                CorrecteurLoc = "A venir"
                else:
                    EventString = "Peer-Evaluation de :"  
                    if type(item["correcteds"]) != str:
                        for j in range(len(item["correcteds"])):
                            Correcteur += item["correcteds"][j]["login"]
                            CorrecteurLoc += requests.get(f'https://api.intra.42.fr/v2/users/{Correcteur}', headers=headers).json()["location"]
                    else:
                        Correcteur = "A venir"
                        CorrecteurLoc = "A venir"
                event_description = f' {Correcteur}\nLocation : {CorrecteurLoc}'
                if event_uid in existing_event_uids:
                    existing_event = existing_event_uids[event_uid]
                    existing_event_description = existing_event.vobject_instance.vevent.description.value
                    
                    if existing_event_description != event_description:
                        existing_event.vobject_instance.vevent.description.value = event_description
                        existing_event.save()
                else:
                    event = Event()
                    event.add('uid', event_uid)
                    event.add('summary', EventString)
                    event.add('dtstart', datetime.strptime(item['begin_at'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC))
                    event.add('dtend', datetime.strptime(item['begin_at'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.UTC) + timedelta(minutes=15))
                    event.add('description', f' {Correcteur}\nLocation : {CorrecteurLoc}')
                    calendar.add_event(event.to_ical())
            
            # Enregistrer le fichier iCal sur le serveur Davical
            ical_data = cal.to_ical()
            davical_url = f'{DAVICAL_URL}/calendars/{DAVICAL_USER}/default.ics'
            response = requests.put(davical_url, data=ical_data, auth=(DAVICAL_USER, DAVICAL_PASS), headers={'Content-Type': 'text/calendar'})
    
    if response.status_code == 201:
        return 'Fichier iCal enregistré avec succès sur le serveur Davical', 201
    else:
        return f'Erreur lors de l\'enregistrement sur le serveur Davical: {response.content}', response.status_code



@app.route('/periodic_update')
def periodic_update():
    while True:
        if loged == True:
            update()
            print('updated')
            time.sleep(120)
    return("stop")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
