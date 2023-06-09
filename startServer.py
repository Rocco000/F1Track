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

@app.route('/constructors')
def get_constructors():
    seasons = db["Seasons"]
    elements = seasons.find()
    years = list()
    for e in elements:
        years.append(e["year"])
    years.sort(reverse=True)
    return render_template("constructorsxSeason.html",s=years)




if __name__ == "__main__":
    app.run(debug=True, port=8000)