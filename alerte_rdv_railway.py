import requests
from bs4 import BeautifulSoup
import os

url = os.environ.get("RDV_URL")
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
print("Page chargee avec succes")
