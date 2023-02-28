import nonebot
from nonebot import on_regex,on_message
from nonebot.exception import StopPropagation
try:
    from nonebot.adapters.cqhttp import Bot, MessageEvent, MessageSegment,GroupMessageEvent,Message
    from nonebot.typing import T_State
except ImportError:
    nonebot.logger.error("Can't find adapters! Abort load!")
    raise ImportError("No support adapter find!")
try:
    import ujson
except:
    import json
import re,os,time
from pathlib import Path
from data_source import *


image_list = {}
custom_face_image_set = on_regex(r"#(自定表情包|自定义表情包|自定表情|自定义表情)设置",priority=10)
@custom_face_image_set.handle()
async def _(bot: Bot, event: GroupMessageEvent,state:T_State):
    global image_list
    args = str(event.get_plaintext()).strip()
    group_id = event.group_id
    if len(args.split(" "))!=2:
        await custom_face_image_set.finish("输入表情名称参数错误！正确的命令格式为:[#自定义表情包设置 表情名称]！")
    face_name = args.split(" ")[-1]
    if not str(group_id) in image_list:
        await custom_face_image_set.finish("请发送一张图片再使用该命令！")
    if not event.get_user_id() in image_list[str(group_id)]:
        await custom_face_image_set.finish("请发送一张图片再使用该命令！")
    if abs(image_list[str(group_id)][event.get_user_id()]["time"] - time.time()) > (5.6*60):
        await custom_face_image_set.finish("你上次发图距离现在的时间太长了请再发送图片后再使用该命令！")
    try:
        state = await customface.save_image_file(face_name=face_name,file=image_list[str(group_id)][event.get_user_id()]["file"],url=image_list[str(group_id)][event.get_user_id()]["url"],group_id=group_id)
    except Exception as e:
        nonebot.logger.error("自定表情设置失败 Res:"+str(e))
        await custom_face_image_set.finish("设置失败！出错了！")
    if not state:
        await custom_face_image_set.finish("设置失败！出错了！")
    await custom_face_image_set.finish("设置成功！")

        
customface = CustomFace()
custom_face_image_handle = on_message(priority=12,block=False)
@custom_face_image_handle.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    global image_list
    if not "group_id" in event.dict():
        return
    group_id = int(event.dict()["group_id"])
    msg_text = event.get_plaintext()
    msg = event.get_message()
    if msg[0].type == "image":
        if not str(group_id) in image_list:
            image_list[f"{group_id}"]={}
        image_list[f"{group_id}"][event.get_user_id()]={"file":msg[0].data["file"],"time":time.time()}
        return
    
    for message in Message(event.message):
        if message.type != "text":
            return
        
    face_name = msg_text.replace("\n","").replace("\t","").replace(" ","")
    if not re.findall("(jpg|png|gif|JPG|PNG|GIF)",face_name):
        return
    if face_name:
        face_name = face_name.replace(".","")
        for not_in_str in ["jpg","png","gif","JPG","PNG","GIF"]:
            face_name = face_name.replace(not_in_str,"")
        face_message_id_file,face_save_path = await customface.search_matcher_face(face_name,group_id)
        if face_message_id_file is not None:
            try:
                data = await bot.get_image(file=face_message_id_file)
            except Exception as e:
                nonebot.logger.error("自动表情包发送失败 Message Error Res:"+str(e))
                await custom_face_image_handle.finish()
            image_msg = MessageSegment.image(data["url"])
        elif face_save_path is not None:
            image_msg = MessageSegment.image(face_save_path)
        else:
            return
        try:
            await custom_face_image_handle.send(image_msg,timeout=30)
        except Exception as e:
            nonebot.logger.error("自动表情包发送失败 Message Send Error Res:"+str(e))
            await custom_face_image_handle.finish("图片资源失效！")
        raise StopPropagation("Stop Handle Message!")
    return