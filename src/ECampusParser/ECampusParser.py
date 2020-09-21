import requests
import os

from io import StringIO
from bs4 import BeautifulSoup
from dotenv import load_dotenv

class ECampus:
  
  def __init__(self):
    self.sess = requests.Session()
  
  def getHTML(self, uri):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_16_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    req = self.sess.get(uri, headers=headers)
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
      if tag.find(attrs={'class': 'label label-course'}).text != "교과":
        continue
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

    prog = []

    try:
      table = soup.find('table', {'class': 'table table-bordered user_progress'})

      rows = table.find('tbody').find_all('tr')
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
        term = searchSpace.split(title + ' 콘텐츠제작도구 \xa0')
        if len(term) > th:
          term = term[th].split(',')[0]
          duedate = term.split(' ~ ')[1]

          prog[i]['duedate'] = duedate

        collisions[title] = th
    except:
      pass

    return prog

  def getAssignments(self, id):
    html = self.getHTML('http://ecampus.kookmin.ac.kr/mod/assign/index.php?id=' + id)
    soup = BeautifulSoup(html, 'html.parser')

    assns = []

    try:
      rows = soup.find('tbody').find_all('tr')

      cell1s = soup.find_all('td', {'class': 'cell c1'})
      cell2s = soup.find_all('td', {'class': 'cell c2'})
      cell3s = soup.find_all('td', {'class': 'cell c3'})

      for i in range(len(cell1s)):
        try:
          title = cell1s[i].text.strip()
          duedate = cell2s[i].text.strip()
          submit = cell3s[i].text.strip()
          assnId = cell1s[i].find('a').get('href').split('id=')[1]

          assns.append({'title': title, 'duedate': duedate, 'submit': submit, 'id': assnId})
        except:
          pass
    except:
      pass
    
    return assns

if __name__ == '__main__':
  load_dotenv()

  MY_USERNAME = os.getenv("MY_USERNAME")
  MY_PASSWORD = os.getenv("MY_PASSWORD")

  ecampus = ECampus()
  print(ecampus.login(MY_USERNAME, MY_PASSWORD))

  subjs = ecampus.getSubjects()

  print(subjs)

  for subj in subjs:
    print('### ' + subj['title'] + ' ###')
    prog = ecampus.getProgress(subj['id'])

    for p in prog:
      print(p)


    assns = ecampus.getAssignments(subj['id'])

    for a in assns:
      print(a)
