# bot.py

from aiocqhttp import CQHttp, Event
import httpx
bot = CQHttp()

group_whitelist = {1077550597:'gkd'}    #群组白名单
alias = 0000    #别名

@bot.on_message('private')
async def _(event: Event):
    msg = event['message']
    if "CQ:image" in msg:
        msg = "[图片]"
    elif "CQ:record" in msg:
        msg = "[语音]"
    elif "CQ:share" in msg:
        msg = "[链接]"
    elif "CQ:music" in msg:
        msg = "[音乐分享]"
    elif "CQ:redbag" in msg:
        msg = "[红包]"
    elif "CQ:forward" in msg:
        msg = "[合并转发]"
    nickName = event['sender']["nickname"]
    async with httpx.AsyncClient() as client:
        await client.post("https://tdtt.top/send",data={'title':'来自QQ的私聊消息','content':'%s:%s'%(nickName,msg),'alias':alias})

@bot.on_message('group')
async def _(event: Event):
    groupId = event['group_id']
    if groupId in group_whitelist:
        msg = event['message']
        if "CQ:image" in msg:
            msg = "[图片]"
        elif "CQ:record" in msg:
            msg = "[语音]"
        elif "CQ:share" in msg:
            msg = "[链接]"
        elif "CQ:music" in msg:
            msg = "[音乐分享]"
        elif "CQ:redbag" in msg:
            msg = "[红包]"
        elif "CQ:forward" in msg:
            msg = "[合并转发]"
        nickName = event['sender']
        groupName = group_whitelist[event['group_id']]
        if nickName['card'] != "":
            nickName = nickName['card']
        elif nickName['card'] == "":
            nickName = nickName['nickname']
        async with httpx.AsyncClient() as client:
            await client.post("https://tdtt.top/send",data={'title':'来自QQ的群聊消息:%s'%groupName,'content':'%s:%s'%(nickName,msg),'alias':alias})
bot.run(host='127.0.0.1', port=8080)
