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


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/getSeasons")
def get_seasons():
    page = request.args.get('page')  # Get the value of the 'page' parameter from the URL
    seasons = db["Seasons"]
    elements = seasons.find()
    years = list()
    for e in elements:
        years.append(e["year"])
    years.sort(reverse=True)
    if page== "drivers":
        return render_template("drivers_season.html", s=years)
    elif page== "constructors":
        return render_template("constructors_season.html",s=years)
    elif page== "races":
        return render_template("races_page.html", s=years)
    elif page== "charts":
        return render_template("charts_season.html", s=years)
    else:
        return render_template("index.html")


@app.route('/getDrivers', methods=['GET'])
def get_drivers_season():
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

    result_list = list()
    for doc in result:
        name = doc["_id"]["name"]
        surname = doc["_id"]["surname"]
        code=""
        if "code" in doc["_id"]:
            code = doc["_id"]["code"]
        result_list.append({'name': name, 'surname': surname, 'code':code})

    return render_template("drivers_listing.html", result_drivers=result_list)


@app.route('/getConstructors')
def get_constructors():
    season = int(request.args.get("year"))
    print("Season: ",season)
    result=db['Races'].aggregate([
        {
            '$match':{
                'year':season
            }
        },
        {
           '$limit' : 1
        },
        {
            '$lookup':{
                'from':'Results',
                'localField':'raceId',
                'foreignField':'raceId',
                'as':'race'
            }
        },
        {
            '$unwind':'$race'
        },
        {
            '$project': {
                'constructorId': '$race.constructorId'
            }
        },
        {
            '$lookup':{
                'from':'Constructors',
                'localField':'constructorId',
                'foreignField':'constructorId',
                'as':'constructors'
            }
        },
        {
            '$unwind':'$constructors'
        },
        {
            '$project': {
                'name': '$constructors.name',
                'nationality':'$constructors.nationality',
                'url':'$constructors.url'
            }
        },
        {
            '$group':{
                '_id':{
                    'name':'$name',
                    'nationality': '$nationality',
                    'url':'$url'
                }
            }
        } 
    ])
    result_list = list()
    for doc in result:
        name = doc["_id"]["name"]
        nationality=doc["_id"]["nationality"]
        url=doc["_id"]["url"]
        result_list.append({'name': name, 'nationality': nationality, 'url': url})
    return render_template("constructors_listing.html", result_constructors=result_list)

@app.route('/getCircuits')
def get_circuits():
    result = db["Circuits"].find()
    return render_template("circuits_page.html", result_circuits=result)

@app.route('/getCharts')
def get_charts():
    season = int(request.args.get("year"))
    result =db["Races"].aggregate([
        {
            '$match':{
                'year':season
            }
        },
        {
            '$project':{
                'raceId':'$raceId'
            }
        },
        {
            '$lookup':{
                'from': 'Results',
                'localField':'raceId',
                'foreignField':'raceId',
                'as':'races_for_season',
            }
        },
        {
            '$unwind': '$races_for_season'
        },
        {
            '$project':{
                'driverId':'$races_for_season.driverId',
                'points':'$races_for_season.points'
            }
        },
        {
            '$lookup':{
                'from': 'Drivers',
                'localField':'driverId',
                'foreignField':'driverId',
                'as':'driver_results',
            }
        },
        {
            '$unwind': '$driver_results'
        },
        {
            '$project':{
                'name':'$driver_results.name',
                'surname':'$driver_results.surname',
                'code':'$driver_results.code',
                'points':'$points'
            }
        },
        {
            '$group':{
                '_id':{
                    'name':'$name',
                    'surname':'$surname',
                    'code':'$code'
                }, 
                'totalPoints':{
                    '$sum' : '$points'
                } 

            }
        },
        {
            '$sort': {
                'totalPoints':-1
            }
        } 
    ])
    result_list = list()
    for doc in result:
        name = doc["_id"]["name"]
        surname=doc["_id"]["surname"]
        code=""
        if "code" in doc["_id"]:
            code=doc["_id"]["code"]
        points=doc["totalPoints"]
        result_list.append({'code': code, 'name': name, 'surname': surname, 'points': points})
    return render_template("chart_listing.html",result_chart=result_list)


if __name__ == "__main__":
    app.run(debug=True, port=8000)


#Per i metodi POST:
# request.form.get("nomecampo")