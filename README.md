# EMOTION API HOW TO

URI : https://lit-spire-48980.herokuapp.com/{{input}}

e.g. : https://lit-spire-48980.herokuapp.com/i%20love%20angry%20birds

Try Detector at https://share.streamlit.io/hellovivien/emotions_detector/app.py

code in streamlit:
```py
        response = requests.get("https://lit-spire-48980.herokuapp.com/{}".format(search_input))
        emotion = response.json()["label"]
```

code in this repo is deployed on heroku (ml is save in file model.bin):
```py
@app.get("/{input}")
def predict(input: str):
    tfidf, model = pickle.load(open('model.bin', 'rb'))
    predictions = model.predict(tfidf.transform([input]))
    label = predictions[0]
    return {'text': input, 'label': label}
```

# LES API ?

## HTTP

![HTTP](https://i.ibb.co/28S2M2S/diagram-of-http-communication-process-fr.png)

\
HTTP signifie « Hypertext Transfer Protocol »
le HTTP détermine comment la page est transmise du serveur au client
On peut donc dire que le HTTP est la langue dans laquelle votre navigateur Web parle au serveur Web afin de lui communiquer ce qui est demandé.

## API

![API](https://i.ibb.co/yPzGv3y/API-page-graphic.png)

Une API est un ensemble de définitions et de protocoles qui facilite la création et l'intégration de logiciels d'applications. API est un acronyme anglais qui signifie « Application Programming Interface », que l'on traduit par interface de programmation d'application.

L'**URI** est l'adresse qui permet d'accéder à L'API et dans laquelle on renseigne les paramètres et le type (GET, POST, DELETE, PUT) de notre requête et si besoin la clé d'authentification pour avoir accès à l'API car la plupart du temps l'utilisation d'une API est limitée ou payante. Un **endpoint** est l'adresse ou se trouve la ressource à proprement dite.



## REST

REST (Representational State Transfer) ou RESTful est un style d’architecture permettant de construire des applications (Web, Intranet, Web Service). Il s’agit d’un ensemble de conventions et de bonnes pratiques à respecter et non d’une technologie à part entière. L’architecture REST utilise les spécifications originelles du protocole HTTP, plutôt que de réinventer une surcouche (comme le font SOAP ou XML-RPC par exemple).

Les 5 règles de REST
Règle n°1 : l’URI comme identifiant des ressources
Règle n°2 : les verbes HTTP comme identifiant des opérations
Règle n°3 : les réponses HTTP comme représentation des ressources
Règle n°4 : les liens comme relation entre ressources
Règle n°5 : un paramètre comme jeton d’authentification

La **documentation** d’une API REST devrait comporter au minimum les éléments suivants :
* la manière de s'authentifier s’il s’agit d'une API privée ;
* la définition des endpoints ;
* les paramètres éventuels ;
* quelques extraits de code ;
* des exemples de requêtes et de réponses.

## Exemples avec POSTMAN

### Giphy

URI : https://api.giphy.com/v1/gifs/random?api_key={{MY SECRET KEY}}&tag={KEYWORD}&rating=g
```js
image url : response.json()["data"]["image_original_url"]
```
### api.openweathermap

URI : http://api.openweathermap.org/data/2.5/weather?q=Lille&appid={{MY SECRET KEY}}
```js
RESPONSE : {"coord":{"lon":3.0586,"lat":50.633},"weather":[{"id":800,"main":"Clear","description":"clear sky","icon":"01d"}],"base":"stations","main":{"temp":301.73,"feels_like":301.19,"temp_min":299.68,"temp_max":302.73,"pressure":1011,"humidity":38},"visibility":10000,"wind":{"speed":0.89,"deg":15,"gust":1.79},"clouds":{"all":0},"dt":1622639246,"sys":{"type":2,"id":2011132,"country":"FR","sunrise":1622605198,"sunset":1622663515},"timezone":7200,"id":2998324,"name":"Lille","cod":200}
```

### TMDB FAVORITE MOVIE


URI : https://api.themoviedb.org/3/movie/550?api_key={{MY SECRET KEY}}

```js
RESPONSE :    
{ "adult": false,
    "backdrop_path": "/rr7E0NoGKxvbkb89eR1GwfoYjpA.jpg",
    "belongs_to_collection": null,
    "budget": 63000000,
    "genres": [
        {
            "id": 18,
            "name": "Drama"
        }
    ],
    "homepage": "http://www.foxmovies.com/movies/fight-club",
    "id": 550,
    "imdb_id": "tt0137523",
    "original_language": "en",
    "original_title": "Fight Club",
    "overview": "A ticking-time-bomb insomniac and a slippery soap salesman channel primal male aggression into a shocking new form of therapy. Their concept catches on, with underground \"fight clubs\" forming in every town, until an eccentric gets in the way and ignites an out-of-control spiral toward oblivion.",
    "popularity": 52.068,
    "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
```