import nonebot
from nonebot import on_message,on_command
from nonebot.exception import StopPropagation
try:
    from nonebot.adapters.cqhttp import Bot, MessageSegment,GroupMessageEvent,Message
    from nonebot.typing import T_State
except ImportError:
    nonebot.logger.error("Can't find adapters! Abort load!")
    raise ImportError("No support adapter find!")
import time
from data_source import *


image_list = {}
custom_emote_image_set = on_command("自定表情包设置",aliases={"自定义表情包设置","自定表情设置","自定义表情设置"},priority=10,block=False)
@custom_emote_image_set.handle()
async def _(bot: Bot, event: GroupMessageEvent,state:T_State):
    global image_list
    args = str(event.get_message()).strip()
    group_id = event.group_id
    emote_name = args
    if not str(group_id) in image_list:
        await custom_emote_image_set.finish("请先发送一张图片再使用该命令！")
    if not event.get_user_id() in image_list[str(group_id)]:
        await custom_emote_image_set.finish("请先发送一张图片再使用该命令！")
    if abs(image_list[str(group_id)][event.get_user_id()]["time"] - time.time()) >= (5.6*60):
        await custom_emote_image_set.finish("你上次发图距离现在的时间太长了请再发送图片后再使用该命令！")
    try:
        state = await customemote.save_image_file(emote_name=emote_name,file=image_list[str(group_id)][event.get_user_id()]["image_file"],url=image_list[str(group_id)][event.get_user_id()]["url"],group_id=group_id)
    except Exception as e:
        nonebot.logger.error("自定表情设置失败 Res:"+str(e))
        await custom_emote_image_set.send("设置失败！出错了！")
        return
    if not state:
        await custom_emote_image_set.finish("设置失败！出错了！")
    reply = MessageSegment.reply(image_list[str(group_id)][event.get_user_id()]["message_id"]) + MessageSegment.text("设置成功！")
    try:
        await custom_emote_image_set.send(reply)
    except:
        await custom_emote_image_set.send("设置成功！")
    await custom_emote_image_set.finish()



customemote = CustomEmote()
custom_emote_image_handle = on_message(priority=12,block=False)
@custom_emote_image_handle.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    global image_list
    group_id = event.group_id
    msg_text = event.get_plaintext()
    msg = event.get_message()
    if msg[0].type == "image":
        if not str(group_id) in image_list:
            image_list[f"{group_id}"]={}
        image_list[f"{group_id}"][event.get_user_id()]={"image_file":msg[0].data["file"],"url":msg[0].data["url"],"message_id":event.message_id,"time":time.time()}
        return
    
    for message in Message(event.message):
        if message.type != "text":
            return
        
    emote_name = msg_text.strip()
    if not await customemote.send_trigger(emote_name):
        return
    
    if emote_name:
        emote_message_id_file,emote_save_path = await customemote.search_matcher_emote(emote_name,group_id)
        if emote_message_id_file is not None:
            try:
                data = await bot.get_image(file=emote_message_id_file)
            except Exception as e:
                nonebot.logger.error("自动表情包发送失败 Message Error Res:"+str(e))
                await custom_emote_image_handle.finish()
            image_msg = MessageSegment.image(data["url"])
        elif emote_save_path is not None:
            image_msg = MessageSegment.image(emote_save_path)
        else:
            return
        try:
            await custom_emote_image_handle.send(image_msg,timeout=30)
        except Exception as e:
            nonebot.logger.error("自动表情包发送失败 Message Send Error Res:"+str(e))
            await custom_emote_image_handle.send("图片资源失效！")
            return
        raise StopPropagation("Stop Handle Message!")
    return
