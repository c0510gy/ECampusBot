from discord.ext.commands import Bot

import os
from ECampusParser.ECampusParser import ECampus
from dotenv import load_dotenv
from tabulate import tabulate

from datetime import datetime

import DataSource.api as API


HELP = '''\
**Welecome to the E-Campus Bot, supporter of your university life and tomorrow**

Made by Sang-geon Yun(Elliot Yun - https://github.com/c0510gy)

```
  !users: 등록된 유저 목록 출력
  !selectuser username: username을 선택
  !show: 남은 강의/과제 목록 출력
  !showAssns: 남은 과제 목록 출력
  !showProgs: 남은 수강 목록 출력
  !subjects: 수강중인 과목 출력
  !progress all: 모든 과목의 강의 출력
  !progress id: 과목 아이디 id에 대한 강의 출력
  !assignments all: 모든 과목의 과제 출력
  !assignments id: 과목 아이디 id에 대한 과제 출력
```
'''


load_dotenv()
ecampus = ECampus()

async def sendMessage(ctx, text):
    idx = 0
    MAX_SIZE = 2000
    while idx < len(text):
        await ctx.send(text[idx:idx + MAX_SIZE])
        idx += MAX_SIZE

def tableGen(headings, rows):
    s = tabulate(rows, headers=headings)
    return s

def videoTime2Seconds(time):
    ret = 0
    try:
        sp = time.split(':')
        for i in range(len(sp)):
            ret = ret * 60 + int(sp[i])
    except:
        pass
    return ret

def getRemainAssns():
    now = datetime.now()

    notSubmittedAssns = []
    missedAssns = []

    subjs = ecampus.getSubjects()

    for subj in subjs:
        assns = ecampus.getAssignments(subj['id'])
        for assn in assns:
            if assn['submit'] != '제출 완료':
                duedate = datetime.strptime(assn['duedate'], '%Y-%m-%d %H:%M')
                if duedate < now:
                    missedAssns.append([subj['title'], assn['title'], assn['duedate']])
                else:
                    duedate = duedate - now
                    due = '{}일 {}시간 {}분 남음'.format(duedate.days, duedate.seconds//3600, (duedate.seconds//60)%60)
                    notSubmittedAssns.append([subj['title'], assn['title'], due, duedate.total_seconds()])
    
    return notSubmittedAssns

def getRemainProgs():
    now = datetime.now()
    
    notProgressed = []
    missedProgress = []

    subjs = ecampus.getSubjects()

    for subj in subjs:
        progs = ecampus.getProgress(subj['id'])
        for prog in progs:
            acktime, takentime = 0, 0

            acktime = videoTime2Seconds(prog['acktime'])
            takentime = videoTime2Seconds(prog['takentime'])

            delta = takentime - acktime

            if delta < 0:
                duedate = datetime.strptime(prog['duedate'], '%Y-%m-%d %H:%M:%S')
                if duedate < now:
                    missedProgress.append([subj['title'], prog['title'], prog['duedate']])
                else:
                    duedate = duedate - now
                    due = '{}일 {}시간 {}분 남음'.format(duedate.days, duedate.seconds//3600, (duedate.seconds//60)%60)
                    notProgressed.append([subj['title'], prog['title'], due, duedate.total_seconds()])
    
    return notProgressed

bot = Bot(command_prefix='!')
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'{bot.user} 에 로그인하였습니다!')

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

@bot.command()
async def help(ctx):
    await ctx.send(HELP)

@bot.command()
async def subjects(ctx):
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    subjs = ecampus.getSubjects()

    s = tableGen(['Subject Name', 'Professor', 'ID'], [[x['title'], x['prof'], x['id']] for x in subjs])
    
    await ctx.send(s)

@bot.command()
async def progress(ctx, *args):
    if len(args) != 1:
        return await ctx.send('과목 아이디가 필요합니다! (모든 과목에 대해 보려면 all)')
    
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    s = ''
    if args[0] == 'all':
        subjs = ecampus.getSubjects()

        for subj in subjs:
            s += '**#####  {}  #####**\n'.format(subj['title'])
            prog = ecampus.getProgress(subj['id'])
            s += tableGen(['강의명', '출석인정 요구시간', '총 학습시간', '진도율', '시청기한'], [[x['title'], x['acktime'], x['takentime'], x['progressPer'], x['duedate']] for x in prog])
            s += '\n\n'
    else:
        prog = ecampus.getProgress(args[0])
        s = tableGen(['강의명', '출석인정 요구시간', '총 학습시간', '진도율', '시청기한'], [[x['title'], x['acktime'], x['takentime'], x['progressPer'], x['duedate']] for x in prog])
    
    await sendMessage(ctx, s)

@bot.command()
async def assignments(ctx, *args):
    if len(args) != 1:
        return await ctx.send('과목 아이디가 필요합니다! (모든 과목에 대해 보려면 all)')
    
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    s = ''
    if args[0] == 'all':
        subjs = ecampus.getSubjects()

        for subj in subjs:
            s += '**#####  {}  #####**\n'.format(subj['title'])
            assns = ecampus.getAssignments(subj['id'])
            s += tableGen(['과제명', '과제 제출기한', '제출상황'], [[x['title'], x['duedate'], x['submit']] for x in assns])
            s += '\n\n'
    else:
        assns = ecampus.getAssignments(args[0])
        s = tableGen(['과제명', '과제 제출기한', '제출상황'], [[x['title'], x['duedate'], x['submit']] for x in assns])
    
    await sendMessage(ctx, s)

@bot.command()
async def showAssns(ctx):
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    notSubmittedAssns = getRemainAssns()
    
    if len(notSubmittedAssns) == 0:
        return await ctx.send('**WOW! 제출할 과제가 없네요!**')
    
    s = '제출할 과제가 **{}개** 남았습니다!\n'.format(len(notSubmittedAssns))

    notSubmittedAssns.sort(key=lambda x: x[3])
    s += tableGen(['과목명', '과제명', '남은 시간'], [x[:3] for x in notSubmittedAssns])
    await sendMessage(ctx, s)

@bot.command()
async def showProgress(ctx):
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    notProgressed = getRemainProgs()
    
    if len(notProgressed) == 0:
        return await ctx.send('**WOW! 들을 강의가 없네요!**')
    
    s = '수강해야할 강의가 **{}개** 남았습니다!\n'.format(len(notProgressed))

    notProgressed.sort(key=lambda x: x[3])
    s += tableGen(['과목명', '강의명', '남은 시간'], [x[:3] for x in notProgressed])
    await sendMessage(ctx, s)

@bot.command()
async def show(ctx):
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    notSubmittedAssns = getRemainAssns()
    notProgressed = getRemainProgs()

    s = ''

    if len(notSubmittedAssns) == 0:
        s += '**WOW! 제출할 과제가 없네요!**\n\n'
    else:
        s += '제출할 과제가 **{}개** 남았습니다!\n'.format(len(notSubmittedAssns))

        notSubmittedAssns.sort(key=lambda x: x[3])
        s += tableGen(['과목명', '과제명', '남은 시간'], [x[:3] for x in notSubmittedAssns]) + '\n\n'
    
    
    if len(notProgressed) == 0:
        s += '**WOW! 들을 강의가 없네요!**'
    else:
        s += '수강해야할 강의가 **{}개** 남았습니다!\n'.format(len(notProgressed))

        notProgressed.sort(key=lambda x: x[3])
        s += tableGen(['과목명', '강의명', '남은 시간'], [x[:3] for x in notProgressed])

    await sendMessage(ctx, s)

@bot.command()
async def users(ctx):
    infos = API.getUserInfos()

    s = tableGen(['User Name', 'e-campus ID'], [[x['name'], x['id']] for x in infos])
    
    await ctx.send(s)

@bot.command()
async def selectuser(ctx, *args):
    if len(args) != 1:
        return await ctx.send('유저 이름이 필요합니다!')

    username = args[0]
    id, pw = API.getUserIDPW(username)

    if ecampus.login(id, pw):
        await ctx.send('유저 선택 성공!')
    else:
        await ctx.send('무언가 잘못되었습니다!')

DISCORD_KEY = os.getenv("DISCORD_KEY")
bot.run(DISCORD_KEY)
