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
  
  def getProgress(self, id):
    html = self.getHTML('http://ecampus.kookmin.ac.kr/report/ubcompletion/user_progress.php?id=' + id)
    soup = BeautifulSoup(html, 'html.parser')

    table = soup.find('table', {'class': 'table table-bordered user_progress'})

    rows = table.find('tbody').find_all('tr')
    prog = []
    for row in rows:
      try:
        title = row.find('td', {'class': 'text-left'}).text.strip()
        acktime = row.find('td', {'class': 'text-center hidden-xs hidden-sm'}).text.strip()
        tags = row.find_all('td', {'class': 'text-center'})
        idx = 1
        if len(tags) >= 4:
          idx = 2
        takentime = tags[idx].text.strip().split('상세보기')[0]
        progressPer = tags[idx + 1].text.strip()

        prog.append({'title': title, 'acktime': acktime, 'takentime': takentime, 'progressPer': progressPer})
      except:
        pass
    
    html = self.getHTML('http://ecampus.kookmin.ac.kr/course/view.php?id=' + id)
    soup = BeautifulSoup(html, 'html.parser')

    totalSection = soup.find('div', {'class': 'total_sections'})
    searchSpace = totalSection.text

    collisions = dict()
    for i in range(len(prog)):
      title = prog[i]['title']
      th = 1
      if title in collisions:
        th = collisions[title] + 1
      term = searchSpace.split(title + ' 콘텐츠제작도구 \xa0')[th].split(',')[0]
      duedate = term.split(' ~ ')[1]

      prog[i]['duedate'] = duedate

      collisions[title] = th

    return prog

  def getAssignments(self, id):
    html = self.getHTML('http://ecampus.kookmin.ac.kr/mod/assign/index.php?id=' + id)
    soup = BeautifulSoup(html, 'html.parser')

    rows = soup.find('tbody').find_all('tr')

    assns = []
    for row in rows:
      title = row.find('td', {'class': 'cell c1'}).text.strip()
      duedate = row.find('td', {'class': 'cell c2'}).text.strip()
      submit = row.find('td', {'class': 'cell c3'}).text.strip()

      assns.append({'title': title, 'duedate': duedate, 'submit': submit})
    
    return assns

if __name__ == '__main__':
  load_dotenv()

  MY_USERNAME = os.getenv("MY_USERNAME")
  MY_PASSWORD = os.getenv("MY_PASSWORD")

  ecampus = ECampus()
  print(ecampus.login(MY_USERNAME, MY_PASSWORD))

  subjs = ecampus.getSubjects()
  prog = ecampus.getProgress(subjs[0]['id'])

  for p in prog:
    print(p)

  assns = ecampus.getAssignments(subjs[0]['id'])

  for a in assns:
    print(a)
