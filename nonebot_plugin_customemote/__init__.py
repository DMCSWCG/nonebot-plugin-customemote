import nonebot
from nonebot import on_regex,on_message,on_command,on_endswith
from nonebot.exception import StopPropagation
from nonebot.typing import T_State
try:
    from nonebot.adapters.cqhttp import Bot, MessageSegment,GroupMessageEvent,Message
except:
    nonebot.logger.warning("Nonebot version look like high then 2.0.0a16 to use high version adapters!")
try:
    from nonebot.adapters.onebot.v11 import Bot, MessageSegment,GroupMessageEvent,Message
except:
    raise ImportError("No support adapter find! Abort load!")
from nonebot.plugin import PluginMetadata
import time,re
from .data_source import *
from .config import *

global_config = nonebot.get_driver().config
plugin_config = Config(**global_config.dict())



__plugin_meta__ = PluginMetadata(
    name="群聊自定义表情包发送器",
    description="用于群聊中设置自定义表情包，并在需要的时候使用对应名称召唤机器人发送表情，不再有打开相册翻表情的烦恼",
    usage="触发方式：指令 + @user/qq/自己/图片\n发送“头像表情包”查看支持的指令",
    config=Config,
    extra={
        "unique_name": "custom_face",
        "example": "设置表情：自定义表情设置 表情名称\n[回复图片]自定表情包设置 滑稽\n召唤表情：表情名称.jpg\n傻了吧唧的.jpg",
        "author": "DMCSWCG <cf136cs@163.com>",
        "version": "0.1.0",
    },
)




customemote = CustomEmote(plugin_config)

custom_emote_image_set = on_command("自定表情包设置",aliases={"自定义表情包设置","自定表情设置","自定义表情设置"},priority=10,block=False)
@custom_emote_image_set.handle()
async def _(bot: Bot, event: GroupMessageEvent,state:T_State):
    image_data_queue = customemote.get_image_data_queue()
    args = str(event.get_message()).strip()
    group_id = event.group_id
    if not args:
        await custom_emote_image_set.finish("请输入需要设置的表情名称")

    if not "two_step_check" in state:
        emote_name = args
        state["emote_name"] = emote_name
    else:
        state["two_step_check_keyword"] = args

    if not str(group_id) in image_data_queue:
        await custom_emote_image_set.finish("请先发送一张图片再使用该命令！")
    if not event.get_user_id() in image_data_queue[str(group_id)]:
        await custom_emote_image_set.finish("请先发送一张图片再使用该命令！")
    if abs(image_data_queue[str(group_id)][event.get_user_id()]["time"] - time.time()) >= (5.6*60):
        image_data_queue[str(group_id)].pop(event.get_user_id())
        customemote.put_image_data_queue(image_data_queue)
        await custom_emote_image_set.finish("你上次发图距离现在的时间太长了请再发送图片后再使用该命令！")
    
    if await customemote.emote_name_is_exist(emote_name,group_id):
        state["two_step_check"]=True
        await custom_emote_image_set.reject("当前设置的表情名称已经存在！是否覆盖设置？")
    else:
        state["set_image"] = True

@custom_emote_image_set.got("two_step_check")
async def _(bot: Bot, event: GroupMessageEvent,state:T_State):
    image_data_queue = customemote.get_image_data_queue()
    if state["two_step_check_keyword"]=="是":
        state["set_image"] = True
        state.pop("two_step_check_keyword")
        state.pop("two_step_check")

    elif state["two_step_check_keyword"]=="否":
        state.pop("emote_name")
        state.pop("two_step_check_keyword")
        state.pop("two_step_check")
        await custom_emote_image_set.finish("取消设置！")
    else:
        if not "wait_count" in state:
            state["wait_count"] = 1
        else :
            state["wait_count"] +=1
        if state["wait_count"]>3:
            state.pop("emote_name")
            state.pop("two_step_check_keyword")
            state.pop("two_step_check")
            state.pop("wait_count")
            await custom_emote_image_set.finish("取消设置！")
    return

@custom_emote_image_set.got("set_image")
async def _(bot: Bot, event: GroupMessageEvent,state:T_State):
    group_id = event.group_id
    image_data_queue = customemote.get_image_data_queue()
    emote_name = state["emote_name"]
    state.pop("emote_name")
    state.pop("set_image")
    try:
        state = await customemote.save_emote_image(emote_name=emote_name,file=image_data_queue[str(group_id)][event.get_user_id()]["image_file"],url=image_data_queue[str(group_id)][event.get_user_id()]["url"],group_id=group_id,user_id=event.get_user_id())
    except Exception as e:
        nonebot.logger.error("自定表情设置失败 Res:"+str(e))
        await custom_emote_image_set.send("设置失败！出错了！")
        return
    if not state:
        await custom_emote_image_set.finish("设置失败！出错了！")
    reply = MessageSegment.reply(image_data_queue[str(group_id)][event.get_user_id()]["message_id"]) + MessageSegment.text("设置成功！")
    try:
        await custom_emote_image_set.send(reply)
    except:
        await custom_emote_image_set.send("设置成功！")
    await custom_emote_image_set.finish()

custom_emote_image_capture = on_message(priority=99,block=False)
@custom_emote_image_capture.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    image_data_queue = customemote.get_image_data_queue()
    group_id = event.group_id
    msg = event.get_message()
    if msg[0].type == "image":
        if not str(group_id) in image_data_queue:
            image_data_queue[f"{group_id}"]={}
        image_data_queue[f"{group_id}"][event.get_user_id()]={"image_file":msg[0].data["file"],"url":msg[0].data["url"],"user_id":event.user_id,"group_id":group_id,"message_id":event.message_id,"time":time.time()}
    return


custom_emote_image_handle = on_endswith(tuple(customemote.active_keyword),priority=12,block=False)
@custom_emote_image_handle.handle()
async def _(bot:Bot,event:GroupMessageEvent,state:T_State):
    group_id = event.group_id
    msg_text = event.get_plaintext()
    
    for message in Message(event.message):
        if message.type != "text":
            await custom_emote_image_handle.finish()

    emote_name = msg_text.strip()
    if not await customemote.send_trigger(emote_name):
        await custom_emote_image_handle.finish()
    
    if emote_name:
        emote_image_file,emote_save_path = await customemote.search_matcher_emote(emote_name,group_id)
        if emote_image_file is not None:
            try:
                data = await bot.get_image(file=emote_image_file)
            except Exception as e:
                nonebot.logger.error("自动表情包发送失败 Message Error Res:"+str(e))
                return
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
    await custom_emote_image_handle.finish()
