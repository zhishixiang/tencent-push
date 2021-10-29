from aiocqhttp import CQHttp, Event
import httpx
bot = CQHttp()
#配置小米推送
MiPush = True #是否开启小米推送，True为是，False为否
alias = "0000" #请在括号内填入别名

#配置FCM推送
FCM = True #是否开启FCM推送，True为是，False为否
key = "0000" #请在括号内填入API KEY

group_whitelist = {1077550597:'gkd'} #群组白名单
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
        if MiPush == True:
            await client.post("https://tdtt.top/send",data={'title':'%s'%nickName,'content':'%s'%(msg),'alias':alias})
        if FCM == True:
            await client.post("http://xdroid.net/api/message",data={'t':'%s'%nickName,'c':'%s'%msg,'k':key})
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
            if MiPush == True:
                await client.post("https://tdtt.top/send",data={'title':'%s'%groupName,'content':'%s:%s'%(nickName,msg),'alias':alias})
            if FCM == True:
                await client.post("http://xdroid.net/api/message",data={'t':'%s'%groupName,'c':'%s:%s'%(nickName,msg),'k':key})
bot.run(host='127.0.0.1', port=8080)
