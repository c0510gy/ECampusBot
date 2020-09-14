from discord.ext.commands import Bot

import os
from ECampusParser.ECampusParser import ECampus
from dotenv import load_dotenv
from tabulate import tabulate

import DataSource.api as API


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

bot = Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user} 에 로그인하였습니다!')

@bot.command()
async def ping(ctx):
    await ctx.send('pong!')

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
