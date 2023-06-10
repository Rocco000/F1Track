from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

app = Flask(__name__)
app.config['SECRET_KEY'] = 'F1_Secret_Session_BD2'
#app.secret_key = 'F1_Secret_Session_BD2'

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

@app.route("/adminHome")
def admin_home():
    return render_template("admin_homepage.html")


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
                'drivers_code': '$drivers_season.code',
                'drivers_url': '$drivers_season.url'
            }
        },
        {
            '$group': {
                '_id':{
                    'name': '$drivers_name',
                    'surname': '$drivers_surname',
                    'code': '$drivers_code',
                    'url':'$drivers_url'
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
        url=doc["_id"]["url"]
        result_list.append({'name': name, 'surname': surname, 'code':code, 'url': url})

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

@app.route('/getRaces', methods=["GET"])
def get_races():
    season = int(request.args.get("year"))
    result = db["Races"].aggregate([
        {
            "$match":{"year":season}
        },
        {
            '$project': {
                "raceId": "$raceId",
                "circuitId": "$circuitId",
                "name": "$name",
                "date": "$date",
                "time": "$time",
            }
        },
        {
            "$lookup":{
                'from':'Circuits',
                'localField':'circuitId',
                'foreignField':'circuitId',
                'as':'related_circuit'
            }
        },
        {
            '$unwind':'$related_circuit'
        },
        {
            '$project': {
                "raceId": "$raceId",
                "name": "$name",
                "date": "$date",
                "time": "$time",
                "name_circuits": "$related_circuit.name"
            }
        },
        {
            '$sort':{'date':1}
        }
    ])
    races = list()
    for doc in result:
        str_date = str(doc["date"])
        doc["date"] = str_date[:10]
        races.append(doc)

    return render_template("races_list.html",races_season=races)

@app.route('/getQualification', methods=["GET"])
def get_qualification():
    race = int(request.args.get("race"))
    result = db["Qualifying"].aggregate([
        {
            '$match':{'raceId':race}
        },
        {
            '$lookup':{
                'from':'Drivers',
                'localField':'driverId',
                'foreignField':'driverId',
                'as':'drivers_qualify' 
            }
        },
        {
            '$unwind':'$drivers_qualify'
        },
        {
            '$project':{
                'name':'$drivers_qualify.name',
                'surname':'$drivers_qualify.surname',
                'code':'$drivers_qualify.code',
                'constructorId':'$constructorId',
                'q1':'$q1',
                'q2':'$q2',
                'q3':'$q3',
                'position':'$position'
            }
        },
        {
            '$lookup':{
                'from':'Constructors',
                'localField':'constructorId',
                'foreignField':'constructorId',
                'as':'drivers_constructor' 
            }
        },
        {
            '$unwind':'$drivers_constructor'
        },
        {
            '$project':{
                'name':'$name',
                'surname':'$surname',
                'code':'$code',
                'constructor':'$drivers_constructor.name',
                'q1':'$q1',
                'q2':'$q2',
                'q3':'$q3',
                'position':'$position'
            }
        }
    ])
    qualification= list()
    for doc in result:
        qualification.append(doc)
    return render_template("qualification_round_list.html", qualification_race= qualification)

@app.route('/getResult', methods=["GET"])
def get_result():
    race = int(request.args.get("race"))
    query_results = db["Results"].aggregate([
        {
            '$match':{'raceId':race}
        },
        {
            '$lookup':{
                'from':'Drivers',
                'localField':'driverId',
                'foreignField':'driverId',
                'as':'drivers_result' 
            }
        },
        {
            '$unwind':'$drivers_result'
        },
        {
            '$project':{
                'name':'$drivers_result.name',
                'surname':'$drivers_result.surname',
                'code':'$drivers_result.code',
                'constructorId':'$constructorId',
                'grid':'$grid',
                'positionText':'$positionText',
                'points':'$points',
                'laps':'$laps',
                'time':'$time',
                'fastestLap':'$fastestLap',
                'statusId':'$statusId'
            }
        },
        {
            '$lookup':{
                'from':'Constructors',
                'localField':'constructorId',
                'foreignField':'constructorId',
                'as':'constructors_result' 
            }
        },
        {
            '$unwind':'$constructors_result'
        },
        {
            '$project':{
                'name':'$name',
                'surname':'$surname',
                'code':'$code',
                'constructor':'$constructors_result.name',
                'grid':'$grid',
                'positionText':'$positionText',
                'points':'$points',
                'laps':'$laps',
                'time':'$time',
                'fastestLap':'$fastestLap',
                'statusId':'$statusId'
            }
        },
        {
            '$lookup':{
                'from':'Status',
                'localField':'statusId',
                'foreignField':'statusId',
                'as':'status_result' 
            }
        },
        {
            '$unwind':'$status_result'
        },
        {
            '$project':{
                'name':'$name',
                'surname':'$surname',
                'code':'$code',
                'constructor':'$constructor',
                'grid':'$grid',
                'positionText':'$positionText',
                'points':'$points',
                'laps':'$laps',
                'time':'$time',
                'fastestLap':'$fastestLap',
                'status':'$status_result.status'
            }
        },
        { '$sort':{'positionText':1}}
    ])

    results= list()
    for doc in query_results:
        results.append(doc)
    return render_template("result_list.html", result_race=results)

@app.route('/searchPage',methods=["GET"])
def load_search_page():
    return render_template("search_page.html")

@app.route('/sortSearch', methods=["GET"])
def sort_search():
    topic = request.args.get("topic")
    match topic:
        case "drivers":
            return render_template("search_drivers.html")
        case "constructors":
            return render_template("")
        case "races":
            return render_template("")
        case "circuits":
            return render_template("")
        case _:
            return render_template("index.html")

@app.route('/driversSearch', methods=["GET"])
def drivers_search():
    field = request.args.get("field")
    value = request.args.get("value")
    if value is None or len(value.strip())==0:
        return render_template("index.html")
    else:  
        if field!="name" and field!="surname" and field!="nationality":
            return render_template("index.html")
        else:
            result = db["Drivers"].find({field:value})
            result_list_app = list(result)
            result_list = list()
            for document in result_list_app:
                str_app = str(document["birthDate"])
                document["birthDate"] = str_app[:10]
                result_list.append(document)
            return render_template("search_result_drivers.html", result_drivers=result_list) 

@app.route('/loginPage',methods=["GET"])
def login():
    if session:
        return render_template("admin_homepage.html")
    return render_template("login.html")


@app.route('/loginCheck',methods=["POST"])
def login_check():
    username= str(request.form.get("username"))
    password= str(request.form.get("password"))
    result=db["Users"].aggregate([
        {
            '$match':{'username':username}
        },
        {
            '$match': {'password':password}
        },
        {
            '$project':{
                'username':'$username',
                'password':'$password'
            }
        }
    ])
    if result.alive:
        session['username'] = username
        return redirect(url_for('admin_home'))
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))    


if __name__ == "__main__":
    app.run(debug=True, port=8000)


#Per i metodi POST:
# request.form.get("nomecampo")