from email import message
import json
from tokenize import group
from flask import Flask,request,jsonify
import json
import requests
import httpx

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

def msgFormat(msg):
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
    elif "戳一戳" in msg:
        msg = "戳了你一下"
    return msg

def getGroupName(groupId):
    length = len(groupInfo["data"])
    for i in range(length):
        if groupId == groupInfo["data"][i]["group_id"]:
            return groupInfo["data"][i]["group_name"]

@app.route("/",methods=['POST'])
async def recvMsg():
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    if json_data["post_type"] == "meta_event":
        if json_data["meta_event_type"] == "heartbeat":
            print("接收心跳信号成功")
    elif json_data["message_type"] == "private":
        nickName = json_data["sender"]["nickname"]
        msg = msgFormat(json_data["message"])
        print("来自%s的私聊消息:%s"%(nickName,msg))
        if MiPush == "True":
            await httpx.AsyncClient().post("https://tdtt.top/send",data={'title':nickName,'content':'%s'%(msg),'alias':KEY})
        elif FCM == "True":
            await httpx.AsyncClient().post("https://wirepusher.com/send",data={'id':KEY,'title':nickName,'message':msg,'type':'privateMsg'})
    elif json_data["message_type"] == "group":
        groupId = json_data["group_id"]
        groupName = getGroupName(groupId)
        nickName = json_data["sender"]["nickname"]
        msg = msgFormat(json_data["message"])
        if groupId in group_whitelist:
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
    