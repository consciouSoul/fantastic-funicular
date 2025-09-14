import httpx
from bs4 import BeautifulSoup


def findLastSubmissionID():
    url = "https://toph.co/submissions"
    r = httpx.get(url)
    soup = BeautifulSoup(r.content, "lxml")
    soup = soup.find("tbody").find("tr", class_="syncer").find("td").text
    return int(soup)


findLastSubmissionID()