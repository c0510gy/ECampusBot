import requests
import os

from io import StringIO
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class ECampus:
  
  def __init__(self):
    self.sess = requests.Session()
  
  def getHTML(self, uri):
    req = self.sess.get(uri)
    html = req.text
    return html
  
  def checkSession(self):
    html = self.getHTML('http://ecampus.kookmin.ac.kr')

    if html.find('로그아웃') == -1:
      return False
    return True
  
  def login(self, id, pw):
    req = self.sess.post('https://ecampus.kookmin.ac.kr/login/index.php', data={
      'username': id,
      'password': pw,
    })

    html = req.text

    return self.checkSession()
  
  def getSubjects(self):
    html = self.getHTML('http://ecampus.kookmin.ac.kr')
    soup = BeautifulSoup(html, 'html.parser')

    # courseList = soup.find('div', {'class': 'course_lists'})
    
    courseTags = soup.find_all('a', {'class': 'course_link'})

    courses = []
    
    for tag in courseTags:
      title = tag.find('h3').text
      if title[-3:] == 'NEW':
        title = title[:-3]
      prof = tag.find('p', {'class': 'prof'}).text
      courseid = tag.get('href').split('id=')[1]
      courses.append({'title': title, 'prof': prof, 'id': courseid})
    
    return courses


if __name__ == '__main__':
  load_dotenv()

  MY_USERNAME = os.getenv("MY_USERNAME")
  MY_PASSWORD = os.getenv("MY_PASSWORD")

  ecampus = ECampus()
  print(ecampus.login(MY_USERNAME, MY_PASSWORD))

  ecampus.getSubjects()
