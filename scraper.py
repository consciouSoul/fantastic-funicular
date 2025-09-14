import httpx
from bs4 import BeautifulSoup


def getSubmissionData(response: httpx.Response):
    if isinstance(response, Exception):
        print(f"Failed to fetch submission: {response}")
        raise response
    
    submissionID = int(response.url.path.split("/")[-1])
    soup = BeautifulSoup(response.content, "lxml")
    

    row = soup.find("tr", attrs={"id": f"trSubmission{submissionID}"})

    # Extract all necessary data in one go
    cells = row.find_all("td")
    timestamp = int(row.find("span", class_="timestamp")["data-timestamp"])
    user = row.find(class_="handle").text.strip()
    problem = cells[3].find("a").get("href").split("/")[-1]
    language = cells[4].text.strip()
    status = cells[5].text.strip()
    executionTime = cells[6].text.strip()
    memoryUsage = cells[7].text.strip()

    # Check for source size
    x = soup.select_one("div.btn.-disabled")
    sourceSize = x.text if x else 0

    # NOTE: The order of these fields matters for the database schema
    data = {
        "submissionID": submissionID,
        "timestamp": timestamp,
        "user": user,
        "problem": problem,
        "language": language,
        "status": status,
        "executionTime": executionTime,
        "memoryUsage": memoryUsage,
        "sourceSize": sourceSize,
    }
    values = list(data.values())
    # submissionID | timestamp | user | problem | language | status | executionTime | memoryUsage | sourceSize
    return values


def getLastSubmissionID():
    response = httpx.get("https://toph.co/submissions")
    soup = BeautifulSoup(response.content, "lxml")

    refresher = soup.find("tr", id="trNewSubmissions")
    lastSubmissionID = int(refresher.nextSibling.find("td").text)

    return lastSubmissionID


if __name__ == "__main__":
    with open("testSubmissionPage.html", "r", encoding="utf-8") as file:
        content = file.read()

    # data = getSubmissionData(None, content)
    # print(data)