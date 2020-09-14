import requests
import os

from io import StringIO
from lxml import etree
from dotenv import load_dotenv

class ECampus:
  
  def __init__(self):
    self.sess = requests.Session()
    self.parser = etree.HTMLParser()
  
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


if __name__ == '__main__':
  load_dotenv()

  MY_USERNAME = os.getenv("MY_USERNAME")
  MY_PASSWORD = os.getenv("MY_PASSWORD")

  ecampus = ECampus()
  print(ecampus.login(MY_USERNAME, MY_PASSWORD))

