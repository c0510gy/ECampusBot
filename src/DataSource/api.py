import csv

def getUserInfos():
  csvfile = open('users.csv', newline='')
  reader = csv.reader(csvfile, delimiter=',')

  infos = []
  for row in reader:
    infos.append({'name': row[0], 'id': row[1]})
  
  return infos

def getUserIDPW(username):
  csvfile = open('users.csv', newline='')
  reader = csv.reader(csvfile, delimiter=',')

  id, pw = '', ''
  for row in reader:
    if row[0] == username:
      id, pw = row[1], row[2]
      break
  
  return id, pw