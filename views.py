from flask import Blueprint, render_template

page = Blueprint(__name__)

#Funzione che rappresenta ciò che sarà mostrato nella homepage
@page.route("/")
def home():
    return render_template("index.html")