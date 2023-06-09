from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

app = Flask(__name__)

#app.register_blueprint(page, url_prefix="/")
#Connecting to MongoDB database
client = MongoClient("mongodb://localhost:27017/")
db = client["F1TrackDB"]

try:
    client.admin.command('ismaster')
    print("Connection to MongoDB successful!")
except ConnectionFailure:
    print("Failed to connect to MongoDB.")

#collection = db["Drivers"] # Sostituisci "nome_collezione" con il nome effettivo della collezione # Recupera tutti gli elementi dalla collezione
#elements = collection.find() # Stampa gli elementi for element in elements: 
#print(elements)

#for element in elements: 
#    content = element["forename"] # Sostituisci "campo_contenuto" con il nome del campo che contiene il contenuto print(content)
#    print(content)


@app.route("/")
def home():
    return render_template("index.html")

@app.route('/loadSeason') #, methods=['GET']
def get_seasons():
    #request.form.get()
    seasons = db["Seasons"]
    elements = seasons.find()
    years = list()
    for e in elements:
        years.append(e["year"])
    years.sort(reverse=True)
    return render_template("driversxSeason.html", s=years)

@app.route('/getDrivers', methods=['GET'])
def getDriversSeason():
    season = int(request.args.get("year"))
    print("Season: ",season)
    result = db['Races'].aggregate([
        {
            '$match':{
                'year':season
            }
        },
        {
            '$lookup': {    
                'from': 'Qualifying',
                'localField': 'raceId',
                'foreignField': 'raceId',
                'as': 'qualify_season'
            }
        },
        {
            '$unwind': '$qualify_season'
        },
        {
           '$project': {
               'drivers_qualify_season': '$qualify_season.driverId',
               'raceId':'raceId',
               'qualifyId':'$qualify_season.qualifyId'
           }
        },
        {
           '$lookup': {
               'from': 'Drivers',
               'localField': 'drivers_qualify_season',
               'foreignField': 'driverId',
               'as': 'drivers_season'
           }
        },
        {
           '$unwind': '$drivers_season'
        },
        {
            '$project': {
                'drivers_name': '$drivers_season.name',
                'drivers_surname': '$drivers_season.surname',
                'drivers_code': '$drivers_season.code'
            }
        },
        {
            '$group': {
                '_id':{
                    'name': '$drivers_name',
                    'surname': '$drivers_surname',
                    'code': '$drivers_code'
                }
            }
        },
        {
             '$sort': { "_id.surname": 1 }
        }
    ])
    print("Risultati ottenuti dalla join:")
    print(result)
    doc = next(result)
    print("Doc 1: ",doc)
    for doc in result:
        print(doc)
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=8000)


#        {
#            '$lookup': {    
#                'from': 'Qualifying',
#                'localField': 'raceId',
#                'foreignField': 'raceId',
#                'as': 'qualify_season'
#            }
#        }
#        {
#            '$unwind': '$qualify_season'
#        },
#        {
#            '$project': {
#                'drivers_qualify_season': '$qualify_season.driverId'
#            }
#        },
#        {
#            '$lookup': {
#                'from': 'Drivers',
#                'localField': 'drivers_qualify_season',
#                'foreignField': 'driverId',
#                'as': 'drivers_season'
#            }
#        },
#        {
#            '$unwind': '$drivers_season'
#        },
#        {
#            '$project': {
#                'drivers_name': '$drivers_season.name',
#                'drivers_surname': '$drivers_season.surname'
#            }
#        }

#Per i metodi POST:
# request.form.get("nomecampo")