from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from datetime import datetime
import pymongo

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
            return render_template("search_constructors.html")
        case "races":
            return redirect(url_for("load_season_race_number"))
        case "circuits":
            return render_template("search_circuits.html")
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
        
@app.route('/constructorsSearch', methods=["GET"])
def constructors_search():
    field = request.args.get("field")
    value = request.args.get("value")
    if value is None or len(value.strip())==0:
        return render_template("index.html")
    else:  
        if field!="name" and field!="nationality":
            return render_template("index.html")
        else:
            result = db["Constructors"].find({field:value})
            result_list = list(result)
            return render_template("search_result_constructors.html", result_constructors=result_list) 

@app.route('/loadSeasonRaceNumber')
def load_season_race_number():
    seasons = db["Seasons"].find()
    seasons_list = list()
    for season in seasons:
        seasons_list.append(season["year"])
    seasons_list.sort(reverse=True)
    return render_template("search_races.html", s=seasons_list)

@app.route('/racesSearch', methods=["GET"])
def races_search():
    race_number = request.args.get("number")
    season = request.args.get("season")
    if race_number is None or season is None or len(race_number.strip())==0 or len(season.strip())==0:
        return render_template("index.html")
    else:
        race_number = int(race_number)
        season = int(season)  
        season_max_number = db["Races"].aggregate([
            {
                '$match':{'year':season}
            },
            {
                '$group':{
                    '_id':{'year':'$year'},
                    'max_value': {'$max': '$raceNumber'}
                }
            },
            {
                '$project':{
                    'max_value':'$max_value'
                }
            }
        ])
        max = 0
        for doc in season_max_number:
            max = doc["max_value"]
        if race_number > max:
            return render_template("index.html")
        else:
            result = db["Races"].aggregate([
                {
                    '$match':{"year":season, "raceNumber":race_number}
                },
                {
                    '$lookup':{
                        'from':'Circuits',
                        'localField':'circuitId',
                        'foreignField':'circuitId',
                        'as':'race_circuit' 
                    }
                },
                {       
                    '$unwind': '$race_circuit'
                },
                {
                    '$project': {
                        'name':'$name',
                        'circuit':'$race_circuit.name',
                        'city':'$race_circuit.city',
                        'date':'$date',
                        'time':'$time',
                        'url':'$url'
                    }
                }
            ])
            result_list = list()
            for doc in result:
                str_app = str(doc["date"])
                doc["date"] = str_app[:10]
                result_list.append(doc)
            return render_template("search_result_races.html", result_races=result_list) 

@app.route('/circuitsSearch', methods=["GET"])
def circuits_search():
    field=request.args.get("field")
    value=request.args.get("value")
    if value is None or len(value.strip())==0:
        return render_template("index.html")
    elif field !="city" and field !="country":
         return render_template("index.html")
    else:
        result= db["Circuits"].find({field:value})
        list_app=list(result)
        result_list=list()
        for doc in list_app:
            result_list.append(doc)
        return render_template("search_result_circuits.html", result_circuits=result_list)

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

@app.route('/adminOperation', methods=["GET"])
def admin_operation():
    if check_session():
        chose = request.args.get("operation")
        if chose is None or len(chose.strip())==0:
            return redirect(url_for("admin_home"))
        else:
            chose = int(chose)
            match chose:
                case 1:
                    return render_template("insert_form.html")
                case 2:
                    result_season = db["Seasons"].find()
                    seasons_list = list()
                    for doc in result_season:
                        seasons_list.append(doc["year"])
                    return render_template("update_form.html", seasons=seasons_list)
                case 3:
                    return render_template("delete_form.html")
                case _:
                    return redirect(url_for("admin_home"))
    else:
        return redirect(url_for("home"))

@app.route('/sortInsert', methods=["GET"])
def sort_insert():
    if check_session():
        collection = request.args.get("collection")
        match collection:
            case "driver":
                return render_template("insert_driver_page.html")
            case "constructor":
                return render_template("insert_constructor_page.html")
            case "race":
                seasons = db["Seasons"].find()
                seasons_list = list()
                for season in seasons:
                    seasons_list.append(season["year"])
                seasons_list.sort(reverse=True)
                circuits=db["Circuits"].find({},{'circuitId':1,'name':1})
                return render_template("insert_race_page.html",s=seasons_list, c=circuits)
            case "circuit":
                return render_template("insert_circuit_page.html")
            case "qualification":
                result = db["Seasons"].find()
                result_list = list()
                for doc in result:
                    result_list.append(doc["year"])
                return render_template("insert_qualification.html", s=result_list)

            case "season":
                return render_template("insert_season_page.html")
            case "result":
                seasons = db["Seasons"].find()
                seasons_list = list()
                for season in seasons:
                    seasons_list.append(season["year"])
                seasons_list.sort(reverse=True)
                return render_template("insert_season_result_page.html", s=seasons_list)
            case _:
                return redirect(url_for("admin_home"))
    else:
        redirect(url_for("home"))

@app.route('/insertDriver', methods=["GET"])
def insert_driver():
    if check_session():
        name = request.args.get("name")
        surname = request.args.get("surname")
        birth = request.args.get("birth")
        nat = request.args.get("nat")
        code = request.args.get("code")
        app_list = list((name, surname, birth, nat))
        if check_string(app_list):
            #Check if the driver is already in the DB
            result_check = db["Drivers"].find({"name":name, "surname":surname, "birthDate":birth})
            result = list(result_check)
            if len(result)>0:
                flash(f"There is already a driver with this data!")
                return redirect(url_for('admin_operation', operation="1"))
            max = get_max_field_value(db["Drivers"], "driverId") +1
            date_format = '%Y-%m-%d'
            date_object = datetime.strptime(birth, date_format)
            insert_result = None
            if code is None or len(code.strip())==0:
                insert_result = db["Drivers"].insert_one({"driverId":max, "name":name, "surname":surname, "birthDate":date_object, "nationality":nat})
            else:
                insert_result = db["Drivers"].insert_one({"driverId":max, "name":name, "surname":surname, "code":code, "birthDate":date_object, "nationality":nat})
            if insert_result.acknowledged:
                flash(f"Driver insert with success!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
        else:
            return redirect(url_for("admin_home"))        
    else:
        return redirect(url_for("home"))

@app.route('/insertCircuit', methods=["GET"])
def insert_circuit():
    if check_session():
        name = request.args.get("name")
        city = request.args.get("city")
        country = request.args.get("country")
        lat = request.args.get("lat")
        long = request.args.get("long")
        alt = request.args.get("alt")
        app_list = list((name, city, country))
        if check_string(app_list):
            #Check if the circuit is already in th DB
            result_check = db["Circuits"].find({"name":name})
            result = list(result_check)
            if len(result)>0:
                flash(f"There is already a circuit with this name!")
                return redirect(url_for('admin_operation', operation="1"))

            max = get_max_field_value(db["Circuits"], "circuitId") +1
            insert_result = None
            if (lat is None or len(lat.strip())==0) and (long is None or len(long.strip())==0) and (alt is None or len(alt.strip())==0):
                #There is not a position
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country})
            elif (not (lat is None or len(lat.strip())==0)) and (long is None or len(long.strip())==0) and (alt is None or len(alt.strip())==0):
                #There is only latitude
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"latitude":lat}})
            elif (lat is None or len(lat.strip())==0) and (not (long is None or len(long.strip())==0)) and (alt is None or len(alt.strip())==0):
                #There is only longitude
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"longitude":long}})
            elif (lat is None or len(lat.strip())==0) and (long is None or len(long.strip())==0) and (not (alt is None or len(alt.strip())==0)):
                #There is only altitude
                alt = int(alt)
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"altitude":alt}})
            elif not((lat is None or len(lat.strip())==0) and (long is None or len(long.strip())==0)) and (alt is None or len(alt.strip())==0):
                #There are latitude and longitude
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"latitude":lat, "longitude":long}})
            elif (lat is None or len(lat.strip())==0) and not((long is None or len(long.strip())==0) and (alt is None or len(alt.strip())==0)):
                #There are longitude and altitude
                alt = int(alt)
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"longitude":long, "altitude":alt}})
            elif (not (lat is None or len(lat.strip())==0)) and (long is None or len(long.strip())==0) and (not (alt is None or len(alt.strip())==0)):
                #There are latitude and altitude
                alt = int(alt)
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"latitude":lat, "altitude":alt}})
            else:
                #There is a full position
                alt = int(alt)
                insert_result = db["Circuits"].insert_one({"circuitId":max, "name":name, "city":city, "country":country, "position":{"latitude":lat, "longitude":long, "altitude":alt}})
            
            if insert_result.acknowledged:
                flash(f"Circuit insert with success!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
    else:
        return redirect(url_for("home"))
    

@app.route('/insertConstructor',methods=["GET"])
def insert_constructor():
    if check_session():
        name=request.args.get("name")
        nationality=request.args.get("nationality")
        url=request.args.get("url")
        app_list=list((name,nationality))
        if check_string(app_list):
            #Check if the constructor is already in the DB
            result_check = db["Constructors"].find({"name":name})
            result = list(result_check)
            if len(result)>0:
                flash(f"There is already a constructor with this name!")
                return redirect(url_for('admin_operation', operation="1"))
            
            max_id=get_max_field_value(db["Constructors"],"constructorId")+1
            insert_result=None
            if url is None or len(url.strip())==0:
                insert_result=db["Constructors"].insert_one({"constructorId":max_id, "name":name, "nationality":nationality})
            else:
                insert_result=db["Constructors"].insert_one({"constructorId":max_id, "name":name, "nationality":nationality, "url": url})
            if insert_result.acknowledged:
                flash(f"Constructor insert with success!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
        else:
            return redirect(url_for("admin_home"))
    else: 
        return redirect(url_for("home"))

@app.route('/insertQualifyGetDriversRaces',methods=["GET"])
def insert_qualify_get_driver():
    if check_session():
        season = request.args.get("year") 
        if season is None or len(season.strip())==0:
            flash(f"You missed the season!")
            return redirect(url_for('admin_operation', operation="1"))
        season = int(season)
        result = db["Races"].find({"year":season})
        first_document = next(result, None)
        if first_document is not None:
            #Season exists
            races_name = list()
            races_name.append({"id":first_document["raceId"], "name":first_document["name"]})

            #Take all the races of the season
            for doc in result:
                races_name.append({"id":doc["raceId"], "name":doc["name"]})
        
            result_drivers = db["Drivers"].find() #Take all the drivers
            result_constructor = db["Constructors"].find() #Take all the constructors
            drivers_list = list()
            constructors_list = list()
            for doc in result_drivers:
                drivers_list.append({"driverId":doc["driverId"], "name_surname":doc["name"]+" "+doc["surname"]})
            for doc in result_constructor:
                constructors_list.append({"constructorId":doc["constructorId"], "name":doc["name"]})
                
            return render_template("insert_qualification2.html", drivers=drivers_list, constructors=constructors_list, races=races_name)
        else:
            flash(f"The season is wrong!")
            return redirect(url_for('admin_operation', operation="1"))
    else: 
        return redirect(url_for("home"))

@app.route('/insertQualify',methods=["GET"])
def insert_qualify():
    if check_session():
        raceId = request.args.get("raceName")
        driverId = request.args.get("driver")
        constructorId = request.args.get("constructor")
        position = request.args.get("position")
        q1 = request.args.get("q1")
        q2 = request.args.get("q2")
        q3 = request.args.get("q3")
        app_list = list((driverId, constructorId, raceId, position, q1))
        if check_string(app_list):
            result_check = db["Qualifying"].find({"driverId":int(driverId), "raceId":int(raceId)})
            result = list(result_check)
            if len(result)>0:
                flash(f"There is already a qualification round for this driver in this race!")
                return redirect(url_for('admin_operation', operation="1"))
            #User inserts the need fields
            max_id=get_max_field_value(db["Qualifying"],"qualifyId")+1
            insert_result = None
            if not ( (q2 is None or len(q2.strip())==0)) and not((q3 is None or len(q3.strip())==0)):
                #q2 and q3 is available
                insert_result = db["Qualifying"].insert_one({"qualifyId":int(max_id), "raceId":int(raceId), "driverId":int(driverId), "constructorId":int(constructorId), "position":int(position), "q1":q1, "q2":q2, "q3":q3})
            elif not ( (q2 is None or len(q2.strip())==0)) and (q3 is None or len(q3.strip())==0):
                #q3 is not available
                insert_result = db["Qualifying"].insert_one({"qualifyId":int(max_id), "raceId":int(raceId), "driverId":int(driverId), "constructorId":int(constructorId), "position":int(position), "q1":q1, "q2":q2})
            elif (q2 is None or len(q2.strip())==0) and not ((q3 is None or len(q3.strip())==0)):
                #q2 is not available but q3 yes -> error
                flash(f"You send the third qualification time without the second qualification time!")
                return redirect(url_for('admin_operation', operation="1"))
            else:
                #q2 and q3 are not available
                insert_result = db["Qualifying"].insert_one({"qualifyId":int(max_id), "raceId":int(raceId), "driverId":int(driverId), "constructorId":int(constructorId), "position":int(position), "q1":q1})
            
            if insert_result.acknowledged:
                flash(f"Added new qualification!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
        else:
            flash(f"You missed some data in the driver insert page!")
            return redirect(url_for('admin_operation', operation="1"))
    else:
        return redirect(url_for("home"))

@app.route('/sortUpdate', methods=["GET"])
def sort_update():
    if check_session():
        collection = request.args.get("collection")
        season = request.args.get("season")
        app_list = list((collection, season))
        if check_string(app_list):
            #Check if the season is in the DB
            check_query = db["Seasons"].find({"year":int(season)})
            first_document = next(check_query, None)
            if first_document is None:
                flash(f"The season is wrong!")
                return redirect(url_for('admin_operation', operation="2"))
            
            race_result = db["Races"].find({"year":int(season)}) #Take all races of a certain season
            race_list = list()
            for doc in race_result:
                race_list.append({"raceId":doc["raceId"], "name":doc["name"]})

            match collection:
                case "result":
                    return render_template("update_select_race.html", races=race_list, flag=1)
                case "qualification":
                    return render_template("update_select_race.html", races=race_list, flag=2)
                case _:
                    return redirect(url_for("admin_home"))
        else:
            flash(f"You missed data in the update section!")
            return redirect(url_for('admin_operation', operation="2"))
    else:
        return redirect(url_for("home"))

@app.route('/loadUpdateResult', methods=["GET"])
def load_update_result():
    if check_session():
        raceId = request.args.get("race")
        if raceId is not None and len(raceId.strip())!=0:
            raceId = int(raceId)
            #Check if the race exists in the DB
            check_query = db["Results"].find({"raceId":raceId})
            first_document = next(check_query, None)
            if first_document is None:
                flash(f"You sent a wrong race!")
                return redirect(url_for('admin_operation', operation="2"))
            
            query_results = db["Results"].aggregate([
                {
                    '$match':{'raceId':raceId}
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
                        'driverId':'$drivers_result.driverId',
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
                        'driverId':'$driverId',
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
                        'driverId':'$driverId',
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

            drivers_result_list = list()
            drivers_name_surname = list()
            for doc in query_results:
                str_app = doc["name"]+" "+doc["surname"]
                drivers_name_surname.append({"driverId_raceId":str(doc["driverId"])+","+str(raceId), "name_surname":str_app})
                drivers_result_list.append(doc)
            
            return render_template("update_result.html", result_race=drivers_result_list, drivers_name_surname=drivers_name_surname)
        else:
            flash(f"You missed the race data!")
            return redirect(url_for('admin_operation', operation="2"))
    else:
        return redirect(url_for("home"))

@app.route('/updateResult', methods=["GET"])
def update_result():
    if check_session():
        driverId = request.args.get("driver")
        points = request.args.get("points")
        driverId, raceId = driverId.split(",")
        app_list = list((driverId, raceId, points))
        if check_string(app_list):
            driverId = int(driverId)
            raceId = int(raceId)
            points = int(points)

            #Check if the race exists in the DB
            check_query = db["Results"].find({"raceId":raceId})
            first_document = next(check_query, None)
            if first_document is None:
                flash(f"The race data are wrong!")
                return redirect(url_for('admin_operation', operation="2"))
            
            #Check if the driver exists in the DB
            check_query = db["Drivers"].find({"driverId":driverId})
            first_document = next(check_query, None)
            if first_document is None:
                flash(f"The driver data are wrong!")
                return redirect(url_for('admin_operation', operation="2"))  

            #Update the result point for a certain driver
            query = {"raceId":raceId, "driverId":driverId}
            new_values = {"$set":{"points":points}}  
            update_query = db["Results"].update_one(query, new_values)

            #Check if the update operation is successful
            if update_query.acknowledged and update_query.modified_count > 0:
                return redirect(url_for('load_update_result', race=raceId))
            else:
                flash(f"Error in the update operation!")
                return redirect(url_for('admin_operation', operation="2"))
        else:
            flash(f"You missed updated points or the driver data!")
            return redirect(url_for('admin_operation', operation="2"))
    else:
        return redirect(url_for("home"))

@app.route('/insertSeason',methods=["GET"])
def insert_season():
    if session:
        year=request.args.get("year")
        url=request.args.get("url")
        app_list=list((year,url))
        if check_string(app_list):
            insert_result=db["Seasons"].insert_one({"year":int(year), "url":url})
            if insert_result.acknowledged:
                flash(f"Season insert with success!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
        else:
            return redirect(url_for("admin_home"))
    else:
        return redirect(url_for("home"))
    

@app.route('/insertRace',methods=["GET"])
def insert_race():
    if session:
        year=request.args.get("year")
        circuitId=request.args.get("circuit")
        name=request.args.get("name")
        date=request.args.get("race-date")
        time=request.args.get("race-time")
        url=request.args.get("url")
        app_list=list((year,circuitId,name,date,time))
        if check_string(app_list):
            year=int(year)
            circuitId=int(circuitId)
            date_format = '%Y-%m-%d'
            date= datetime.strptime(date, date_format)
            raceId=get_max_field_value(db["Races"],"raceId")+1
            race_number_result=db["Races"].aggregate([
                {
                    '$match': {'year':year}
                },
                {
                    '$group':{
                        '_id':{'year':'$year'},
                        'max_value': {'$max': '$raceNumber'}
                    }
                },
                {
                    '$project':{
                        'max_value':'$max_value'
                    }
                }
            ])
            for doc in race_number_result:
                raceNumber=doc["max_value"]+1
            if url is None or len(url.strip())==0:
                insert_result=db["Races"].insert_one({"raceId": raceId, "year": year, "raceNumber": raceNumber, "circuitId": circuitId, "name": name, "date":date ,"time": time})
            else:
                insert_result=db["Races"].insert_one({"raceId": raceId, "year": year, "raceNumber": raceNumber, "circuitId": circuitId, "name": name, "date":date ,"time": time,"url": url})
            if insert_result.acknowledged:
                flash(f"Race insert with success!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
        else:
            return redirect(url_for("admin_home"))
    else:
        return redirect(url_for("home"))
    

@app.route('/insertResultData',methods=["GET"])
def insert_result_data():
    if session:
        season=request.args.get("year")
        season=int(season)
        races= db["Races"].find({'year': season},{'raceId':1,'name':1,'circuitId':1})
        drivers = db['Drivers'].find({},{'driverId':1,'name':1, 'surname':1})
        status=db["Status"].find({},{'statusId':1,'status':1})
        constructors=db["Constructors"].find({},{'constructorId':1,'name':1})
        races_list=list()
        for race in races:
            races_list.append(race)
        return render_template("insert_result_page.html", races=races_list,drivers=drivers,status_list=status,constructors=constructors)
    else:
        return redirect(url_for("home"))


@app.route('/insertResult',methods=["GET"])
def insert_result():
    if session:
        resultId=get_max_field_value(db["Results"],"resultId")+1
        raceId=request.args.get("race")
        driverId=request.args.get("driver")
        constructorId=request.args.get("constructor")
        check_validity=db["Results"].find({'raceId':int(raceId), 'driverId':int(driverId)},{})
        first_document = next(check_validity, None)
        if first_document is not None:
            flash(f"This result already exist!")
            return redirect(url_for('admin_operation', operation="1")) 
        carNumber=request.args.get("car-number")
        grid=request.args.get("grid")
        position=request.args.get("position")
        positionText=request.args.get("position-text")
        points=request.args.get("points")
        laps=request.args.get("laps")
        time=request.args.get("time")
        fastestLap=request.args.get("fastest-lap")
        fastestLapTime=request.args.get("fastest-lap-time")
        fastestLapSpeed=request.args.get("fastest-lap-speed")
        status=request.args.get("status")

        app_list=list((raceId,driverId,grid,position,positionText,points,laps,time,fastestLap,fastestLapTime,fastestLapSpeed,status))
        if check_string(app_list):
            raceId=int(raceId)
            driverId=int(driverId)
            constructorId=int(constructorId)
            grid=int(grid)
            position=int(position)
            if positionText.isdigit:
                positionText=int(positionText)
            points=int(points)
            laps=int(laps)
            fastestLap=int(fastestLap)
            status=int(status)
            if carNumber is None or len(carNumber.strip())==0:
                insert_result=db["Results"].insert_one({"resultId": resultId, "raceId": raceId, "driverId": driverId, "constructorId": constructorId, "grid": grid, "position": position, "positionText": positionText, "points": points, "laps": laps, "time": time, "fastestLap": fastestLap, "fastestLapTime": fastestLapTime, "fastestLapSpeed": fastestLapSpeed, "statusId": status})
            else:
                insert_result=db["Results"].insert_one({"resultId": resultId, "raceId": raceId, "driverId": driverId, "constructorId": constructorId, "carNumber":carNumber, "grid": grid, "position": position, "positionText": positionText, "points": points, "laps": laps, "time": time, "fastestLap": fastestLap, "fastestLapTime": fastestLapTime, "fastestLapSpeed": fastestLapSpeed, "statusId": status})
            if insert_result.acknowledged:
                flash(f"Race insert with success!")
            else:
                flash(f"Insert NOT done!")
            return redirect(url_for('admin_operation', operation="1"))
        else:
            return redirect(url_for("admin_home"))
    else:
        return redirect(url_for("home"))


def check_session():
    if session:
        return True
    else:
        return False

def check_string(words):
    for element in words:
        if element is None or len(element.strip())==0:
            return False
        
    return True
            
def get_max_field_value(collection, field):
    pipeline = [
        {"$group": {"_id": None, "max_value": {"$max": "$"+field}}}
    ]
    result = list(collection.aggregate(pipeline))
    max_value = result[0]["max_value"] if result else None
    return max_value

if __name__ == "__main__":
    app.run(debug=True, port=8000)


#Per i metodi POST:
# request.form.get("nomecampo")