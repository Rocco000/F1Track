from flask import Blueprint

page = Blueprint(__name__, "homepage")

@page.route("/")
def home():
    return "Hello F1 supporter!"