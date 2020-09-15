from discord.ext.commands import Bot

import os
from ECampusParser.ECampusParser import ECampus
from dotenv import load_dotenv
from tabulate import tabulate

from datetime import datetime, timedelta

import DataSource.api as API

import asyncio


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

bot = Bot(command_prefix='!')
bot.remove_command('help')

def getKRTime():
    utcnow = datetime.utcnow()
    timeGap = timedelta(hours=9)
    return utcnow + timeGap

def get_channel(channels, channel_name):
    for channel in bot.get_all_channels():
        if channel.name == channel_name:
            return channel
    return None

async def sendMessage(ctx, text):
    idx = 0
    MAX_SIZE = 2000
    while idx < len(text):
        await ctx.send(text[idx:idx + MAX_SIZE])
        idx += MAX_SIZE

def tableGen(headings, rows):
    s = tabulate(rows, headers=headings)
    return '```{}```'.format(s)

def videoTime2Seconds(time):
    ret = 0
    try:
        sp = time.split(':')
        for i in range(len(sp)):
            ret = ret * 60 + int(sp[i])
    except:
        pass
    return ret

def getRemainAssns(ecam):
    now = getKRTime()

    notSubmittedAssns = []
    missedAssns = []

    subjs = ecam.getSubjects()

    for subj in subjs:
        assns = ecam.getAssignments(subj['id'])
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

def getRemainProgs(ecam):
    now = getKRTime()
    
    notProgressed = []
    missedProgress = []

    subjs = ecam.getSubjects()

    for subj in subjs:
        progs = ecam.getProgress(subj['id'])
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

def getRemainAssnsStr(ecam):
    notSubmittedAssns = getRemainAssns(ecam)
    
    if len(notSubmittedAssns) == 0:
        return '**WOW! 제출할 과제가 없네요!**'
    
    s = '제출할 과제가 **{}개** 남았습니다!\n'.format(len(notSubmittedAssns))

    notSubmittedAssns.sort(key=lambda x: x[3])
    s += tableGen(['과목명', '과제명', '남은 시간'], [x[:3] for x in notSubmittedAssns])
    return s

def getRemainProgsStr(ecam):
    notProgressed = getRemainProgs(ecam)
    
    if len(notProgressed) == 0:
        return '**WOW! 들을 강의가 없네요!**'
    
    s = '수강해야할 강의가 **{}개** 남았습니다!\n'.format(len(notProgressed))

    notProgressed.sort(key=lambda x: x[3])
    s += tableGen(['과목명', '강의명', '남은 시간'], [x[:3] for x in notProgressed])
    return s

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
    
    s = getRemainAssnsStr(ecampus)
    
    await sendMessage(ctx, s)

@bot.command()
async def showProgress(ctx):
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')
    
    s = getRemainProgsStr(ecampus)
    
    await sendMessage(ctx, s)

@bot.command()
async def show(ctx):
    if not ecampus.checkSession():
        return await ctx.send('선택된 유저 정보가 없습니다!')

    s = getRemainAssnsStr(ecampus) + '\n\n' + getRemainProgsStr(ecampus)

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

finishedAssns = dict()

def getFnished():
    ecampus2 = ECampus()
    
    infos = API.getUserInfos()
    for info in infos:
        username = info['name']
        id, pw = API.getUserIDPW(username)
        if not ecampus2.login(id, pw):
            continue
        
        finishedAssns[username] = set()

        subjs = ecampus2.getSubjects()
        for subj in subjs:
            assns = ecampus2.getAssignments(subj['id'])

            for assn in assns:
                if assn['submit'] == '제출 완료':
                    finishedAssns[username].add(assn['id'])

async def manageDiff(botChannel):
    ecampus2 = ECampus()
    
    infos = API.getUserInfos()
    for info in infos:
        username = info['name']
        id, pw = API.getUserIDPW(username)
        if not ecampus2.login(id, pw):
            continue
        subjs = ecampus2.getSubjects()
        for subj in subjs:
            assns = ecampus2.getAssignments(subj['id'])

            for assn in assns:
                if assn['submit'] == '제출 완료':
                    if not assn['id'] in finishedAssns[username]:
                        finishedAssns[username].add(assn['id'])

                        ss = '**WOW!** **{}**님이 **{}**과목의 과제 **{}**를 제출 완료했습니다!'.format(username, subj['title'], assn['title'])
                        await sendMessage(botChannel, ss)

alertTimes = set([9, 13, 18])
async def loop():
    lastTime = None
    getFnished()
    botChannel = None
    while botChannel is None:
        await asyncio.sleep(5)
        botChannel = get_channel(bot.get_all_channels(), 'e-campus-bot')
    while True:
        await asyncio.sleep(60)

        await manageDiff(botChannel)

        now = getKRTime()
        curTime = str(now.day) + str(now.hour)
        if now.hour in alertTimes and curTime != lastTime:
            lastTime = str(now.day) + str(now.hour)
            
            ecampus2 = ECampus()
            
            infos = API.getUserInfos()
            for info in infos:
                username = info['name']
                id, pw = API.getUserIDPW(username)
                ss = '**##### {} #####**\n'.format(username)
                if not ecampus2.login(id, pw):
                    ss += '무언가 잘못되었습니다!!'
                else:
                    ss += getRemainAssnsStr(ecampus2) + '\n' + getRemainProgsStr(ecampus2)
                
                await sendMessage(botChannel, ss)


bot.loop.create_task(loop())

DISCORD_KEY = os.getenv("DISCORD_KEY")
bot.run(DISCORD_KEY)
