from email import message
from email.errors import FirstHeaderLineIsContinuationDefect
from tokenize import group
from flask import Flask,request,jsonify
import json
import requests
import httpx
import urllib.parse
import re

try:
    with open("config.json","r",encoding = 'UTF-8') as f:
        config = json.load(f)
    group_whitelist = config["WhiteList"]
    MiPush = config["MiPush"]
    FCM = config["FCM"]
    KEY = config["KEY"]
except:
    print("读取配置文件异常,请检查配置文件是否存在或语法是否有问题")
    assert()

try:
    groupInfo = json.loads(requests.get("http://localhost:5700/get_group_list").text)
    userId = json.loads(requests.get("http://localhost:5700/get_login_info").text)["data"]["user_id"]
except:
    print("无法从go-cqhttp获取信息,请检查go-cqhttp是否运行或端口配置是否正确")
    assert()

app = Flask(__name__)

def msgFormat(rawMsg1):
    if "CQ:image" in rawMsg1:
        cqcode = re.findall('\[CQ:image.*?]', rawMsg1)
        for code in cqcode:
            imageurl = re.findall('(?<=.image,url=).*?(?=,subType=)', code)
            imageurl = ' '.join(imageurl)
            renew = '[图片 ' + imageurl + ']'
            msg = rawMsg1.replace(code, renew)
        else:
            cqcode = re.findall('\[CQ:image.*?]', rawMsg1)
            for code in cqcode:
                msg = rawMsg1.replace(code, '[图片]')
        msg = msg
    elif "CQ:record" in rawMsg1:
        msg = "[语音]"
    elif "CQ:share" in rawMsg1:
        msg = "[链接]"
    elif "CQ:music" in rawMsg1:
        msg = "[音乐分享]"
    elif "CQ:redbag" in rawMsg1:
        msg = "[红包]"
    elif "CQ:forward" in rawMsg1:
        msg = "[合并转发]"
    elif "CQ:video" in rawMsg1:
        msg = "[视频]"
    elif "CQ:reply" in rawMsg1:
        cqcode = re.findall('\[CQ:reply.*?]', rawMsg1)
        replymsg = re.findall('(?<=\[CQ:reply,text=).*?(?=,qq=)', cqcode)
        replyid = re.findall('(?<=\,qq=).*?(?=,time=)', cqcode)
        replymsg = ' '.join(replymsg)
        replyid = ' '.join(replyid)
        renew = '回复 ' + ' ' + replyid + '%0A'
        msg = rawMsg1.replace(code, renew)
    elif "戳一戳" in rawMsg1:
        msg = "戳了你一下"
    elif "CQ:at" in rawMsg1:
        atid = re.findall('(?<=qq=).*?(?=])', rawMsg1)
        for uid in atid:
            atimfurl = 'http://localhost:5700/get_group_member_info?group_id' + str(groupId) + "?user_id=" + str(uid)
            imf = json.loads(requests.get(atimfurl).content)
            regex1 = re.compile(r'\[CQ:at,qq=' + uid + ']')
            cqcode = regex1.search(rawMsg1)
            cqcode = (cqcode.group())
            if imf["data"]["card"] != "":
                at = "@" + imf["data"]["card"] + " "
            else:
                at = "@" + imf["data"]["nickname"] + " "
            msg = rawMsg1.replace(cqcode, at)
    elif 'com.tencent.miniapp' in rawMsg1:
        minijson = json.loads(re.findall('(?<=\[CQ:json,data=).*?(?=])', rawMsg1))
        mini_title = minijson["prompt"]
        if "detail_1" in rawMsg1:
            mini_url = urllib.parse.quote(minijson["meta"]["detail_1"]["qqdocurl"])
            mini_desc = minijson["meta"]["detail_1"]["desc"]
        else:
            mini_url = ""
            mini_desc = ""
            msg = mini_title + "%0A" + mini_desc
    elif "com.tencent.structmsg" in rawMsg1:
        structjson = json.loads(re.findall('(?<=\[CQ:json,data=).*?(?=])', rawMsg1))
        structtitle = structjson["prompt"]
        msg = structtitle
    else:
        msg = rawMsg1
    return msg

def getGroupName(groupId):
    length = len(groupInfo["data"])
    for i in range(length):
        if groupId == groupInfo["data"][i]["group_id"]:
            return groupInfo["data"][i]["group_name"]

@app.route("/",methods=['POST'])
async def recvMsg():
    global groupId
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    if json_data["post_type"] == "meta_event":
        if json_data["meta_event_type"] == "heartbeat":
            print("接收心跳信号成功")
    elif json_data["post_type"] == "request":
        if json_data["request_type"] == "friend":
            friendId = json_data["user_id"]
            print("新的好友添加请求：%s"%friendId)
            if MiPush == "True":
                await httpx.AsyncClient().post("https://tdtt.top/send",data={'title':"新的好友添加请求",'content':'%s想要添加您为好友'%friendId,'alias':KEY})
            elif FCM == "True":
                await httpx.AsyncClient().post("https://wirepusher.com/send",data={'id':KEY,'title':"新的好友添加请求",'message':'%s想要添加您为好友'%friendId,'type':'FriendAdd'})            

    elif json_data["message_type"] == "private":
        nickName = json_data["sender"]["nickname"]
        rawMsg = json_data["message"]
        msg = msgFormat(rawMsg)
        print("来自%s的私聊消息:%s"%(nickName,msg))
        if MiPush == "True":
            await httpx.AsyncClient().post("https://tdtt.top/send",data={'title':nickName,'content':msg,'alias':KEY})
        elif FCM == "True":
            await httpx.AsyncClient().post("https://wirepusher.com/send",data={'id':KEY,'title':nickName,'message':msg,'type':'privateMsg'})
    elif json_data["message_type"] == "group":
        groupId = json_data["group_id"]
        groupName = getGroupName(groupId)
        nickName = json_data["sender"]["nickname"]
        msg = msgFormat(rawMsg)
        if groupId in group_whitelist:
            print("群聊%s的消息:%s:%s"%(groupName,nickName,msg))
            if MiPush == "True":
                await httpx.AsyncClient().post("https://tdtt.top/send",data={'title':'%s'%groupName,'content':'%s:%s'%(nickName,msg),'alias':KEY})
            if FCM == "True":
                await httpx.AsyncClient().post("https://wirepusher.com/send",data={'id':'%s'%KEY,'title':groupName,'message':'%s:%s'%(nickName,msg),'type':'groupMsg'})
        elif "[CQ:at,qq=%s]"%userId in msg:
            msg = msg.replace("[CQ:at,qq=%s]"%userId,"[有人@我]")
            print("群聊%s有人@我:%s:%s"%(groupName,nickName,msg))
            if MiPush == "True":
                await httpx.AsyncClient().post("https://tdtt.top/send",data={'title':'%s'%groupName,'content':'%s:%s'%(nickName,msg),'alias':KEY})
            if FCM == "True":
                await httpx.AsyncClient().post("https://wirepusher.com/send",data={'id':'%s'%KEY,'title':groupName,'message':'%s:%s'%(nickName,msg),'type':'groupMsg'})            
    return "200 OK"

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
    