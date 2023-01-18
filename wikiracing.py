# pylint: disable=C0301, w0622, w0621, R1722, R1710, R0914, C0103
"""Main module."""
from typing import List
import requests
from bs4 import BeautifulSoup
import psycopg2
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


LINKS_PER_PAGES = 200


def connect(data):
    """Connector to web app(requests per minute are 100)."""
    session = requests.Session()
    retries = Retry(connect=100, backoff_factor=0.06)
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    return session.get(data)


class WikiRacer:
    """Class for parse wiki."""

    def find_path(self, start: str, finish: str) -> List[str]:
        """Download articles from the web app."""
        list = []
        path1 = f"https://uk.wikipedia.org/w/index.php?title=Спеціальна:Посилання_сюди/{start}&limit={LINKS_PER_PAGES}"
        path2 = f"https://uk.wikipedia.org/w/index.php?title=Спеціальна:Посилання_сюди/{finish}&limit={LINKS_PER_PAGES}"
        try:
            result1 = connect(path1).text
            result2 = connect(path2).text
        except requests.ConnectionError:
            print("Помилка! Немає звя'зку")
            quit()
        else:
            soup1 = BeautifulSoup(result1, "lxml")
            soup2 = BeautifulSoup(result2, "lxml")
            detail1 = soup1.find(id="mw-whatlinkshere-list").find_all("li")
            detail2 = soup2.find(id="mw-whatlinkshere-list").find_all("li")
            list1 = [i.find("a").get_text() for i in detail1]
            list2 = [i.find("a").get_text() for i in detail2]
            list.append(list1)
            list.append(list2)
            return list


    def get_links_count(self, start: str, finish: str) -> List[str]:
        """Download and count links from the web app."""
        list = []
        path1 = f"https://uk.wikipedia.org/w/index.php?title=Спеціальна:Посилання_сюди/{start}&limit=2000"
        path2 = f"https://uk.wikipedia.org/w/index.php?title=Спеціальна:Посилання_сюди/{finish}&limit=2000"
        result1 = connect(path1).text
        result2 = connect(path2).text
        soup1 = BeautifulSoup(result1, "lxml")
        soup2 = BeautifulSoup(result2, "lxml")
        detail1 = soup1.find(id="mw-whatlinkshere-list").find_all("li")
        detail2 = soup2.find(id="mw-whatlinkshere-list").find_all("li")
        list.append(len(detail1))
        list.append(len(detail2))
        return list


    def get_links_to_other_articles(self, start: str, finish: str) -> List[str]:
        """Download and count links to other resource from web app."""
        list = []
        path1 = f"https://uk.wikipedia.org/wiki/{start}"
        path2 = f"https://uk.wikipedia.org/wiki/{finish}"
        result1 = connect(path1).text
        result2 = connect(path2).text
        soup1 = BeautifulSoup(result1, "lxml")
        soup2 = BeautifulSoup(result2, "lxml")
        detail1 = soup1.find(id="bodyContent").find_all("a")
        detail2 = soup2.find(id="bodyContent").find_all("a")
        list.append(len(detail1))
        list.append(len(detail2))
        return list


    def get_descendants(self, start: str, finish: str) -> List[str]:
        """Download and count descendants of the second level from web app."""
        list = []

        path1 = f"https://uk.wikipedia.org/wiki/{start}"
        path2 = f"https://uk.wikipedia.org/wiki/{finish}"

        result1 = connect(path1).text
        result2 = connect(path2).text

        soup1 = BeautifulSoup(result1, "lxml")
        soup2 = BeautifulSoup(result2, "lxml")

        detail1 = soup1.find(id="bodyContent").find(id="contentSub", recursive=False)
        detail2 = soup1.find(id="bodyContent").find(
            id="mw-content-text", recursive=False
        )
        detail3 = soup1.find(id="bodyContent").find(id="catlinks", recursive=False)

        detail4 = soup2.find(id="bodyContent").find(id="contentSub", recursive=False)
        detail5 = soup2.find(id="bodyContent").find(
            id="mw-content-text", recursive=False
        )
        detail6 = soup2.find(id="bodyContent").find(id="catlinks", recursive=False)

        total1 = len(detail1) + len(detail2) + len(detail3)
        total2 = len(detail4) + len(detail5) + len(detail6)

        list.append(total1)
        list.append(total2)

        return list


racer = WikiRacer()


first = input("Введіть першу назву статті: ").replace(" ", "_")
second = input("Введіть другу назву статті: ").replace(" ", "_")


connection = psycopg2.connect(
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432,
    database="postgres",
)

connection_cursor = connection.cursor()

connection_cursor.execute(
    f"""SELECT links_name FROM articles WHERE article_name='{first}';"""
)
result1 = connection_cursor.fetchall()
connection_cursor.execute(
    f"""SELECT links_name FROM articles WHERE article_name='{second}';"""
)
result2 = connection_cursor.fetchall()

if result1 and result2:
    print("Обидві статті вже иснують в базі даннних ")
elif result1:
    print(
        f"Статті {second} не існуює у базі данних, виконується процес завантаження з ресурсу ......."
    )
    values = racer.find_path(first, second)
    links_count = racer.get_links_count(first, second)[1]
    links_in_article = racer.get_links_to_other_articles(first, second)[1]
    descendants = racer.get_descendants(first, second)[1]
    second_article = ", ".join(values[1]).replace("'", '""')
    connection_cursor.execute(
        f"""INSERT INTO articles (article_name, links_name, links_count, links_in_article, descendants)
      VALUES ('{second}', '{second_article}', '{links_count}', '{links_in_article}', '{descendants}');"""
    )
    connection.commit()
    connection.close()
    print("Процес завантаження завершено!")
elif result2:
    print(
        f"Статті {first} не існуює у базі данних, виконується процес завантаження з ресурсу ......."
    )
    values = racer.find_path(first, second)
    links_count = racer.get_links_count(first, second)[0]
    links_in_article = racer.get_links_to_other_articles(first, second)[0]
    descendants = racer.get_descendants(first, second)[0]
    first_article = ", ".join(values[0]).replace("'", '""')
    connection_cursor.execute(
        f"""INSERT INTO articles (article_name, links_name, links_count, links_in_article, descendants)
        VALUES ('{first}', '{first_article}', '{links_count}', '{links_in_article}', '{descendants}');"""
    )
    connection.commit()
    connection.close()
    print("Процес завантаження завершено!")
else:
    print(
        f"Статтей {first} та {second} не існуює у базі данних, виконується процес завантаження з ресурсу ......."
    )
    values = racer.find_path(first, second)
    first_links_count = racer.get_links_count(first, second)[0]
    first_links_in_article = racer.get_links_to_other_articles(first, second)[0]
    first_descendants = racer.get_descendants(first, second)[0]
    first_article = ", ".join(values[0]).replace("'", '""')
    second_article = ", ".join(values[1]).replace("'", '""')
    second_links_count = racer.get_links_count(first, second)[1]
    second_links_in_article = racer.get_links_to_other_articles(first, second)[1]
    second_descendants = racer.get_descendants(first, second)[1]
    connection_cursor.execute(
        f"""INSERT INTO articles (article_name, links_name, links_count, links_in_article, descendants)
        VALUES ('{first}', '{first_article}', '{first_links_count}', '{first_links_in_article}', '{first_descendants}');"""
    )
    connection_cursor.execute(
        f"""INSERT INTO articles (article_name, links_name, links_count, links_in_article, descendants)
        VALUES ('{second}', '{second_article}', '{second_links_count}', '{second_links_in_article}', '{second_descendants}');"""
    )
    connection.commit()
    connection.close()
    print("Процес завантаження завершено!")
