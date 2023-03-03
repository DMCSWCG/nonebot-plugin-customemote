import nonebot
from nonebot import on_message, on_command, on_endswith
from nonebot.typing import T_State
from nonebot.params import ArgPlainText, CommandArg
from nonebot.matcher import Matcher
from nonebot.adapters import Message
from typing import Union
try:
    from nonebot.adapters.cqhttp import Bot, MessageSegment, GroupMessageEvent, Message
except ModuleNotFoundError as _:
    nonebot.logger.warning(
        "Nonebot version look like high then 2.0.0a16 to use high version adapters!"
    )
    try:
        from nonebot.adapters.onebot.v11 import Bot, MessageSegment, GroupMessageEvent, Message
    except ModuleNotFoundError as _:
        raise ImportError("No support adapter find! Abort load!")
from nonebot.plugin import PluginMetadata
import time, traceback
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
        "unique_name": "custom_emote",
        "example":
        "设置表情：自定义表情设置 表情名称\n[回复图片]自定表情包设置 滑稽\n召唤表情：表情名称.jpg\n傻了吧唧的.jpg",
        "author": "DMCSWCG <cf136cs@163.com>",
        "version": "0.1.0",
    },
)


customemote = CustomEmote(plugin_config)

custom_emote_image_set = on_command("自定表情包设置",
                                    aliases={"自定义表情包设置", "自定表情设置", "自定义表情设置"},
                                    priority=10,
                                    block=False)


@custom_emote_image_set.handle()
async def _sethandle(bot: Bot,
                     event: GroupMessageEvent,
                     matcher: Matcher,
                     state: T_State,
                     args: Message = CommandArg()):
    image_data_queue = await customemote.get_image_data_queue()
    at_user_id = await get_at_user_id(Message(event.get_message()))
    user_id = event.get_user_id() if at_user_id is None else at_user_id
    args = args.extract_plain_text()
    group_id = event.group_id
    state["max_try"] = 3    # 三次重试
    emote_name = args
    if not emote_name:
        await custom_emote_image_set.finish("请输入需要设置的表情名称")
    if not str(group_id) in image_data_queue:
        await custom_emote_image_set.finish("请先发送一张图片再使用该命令！")
    if not event.get_user_id() in image_data_queue[str(group_id)]:
        await custom_emote_image_set.finish("请先发送一张图片再使用该命令！")
    if abs(image_data_queue[str(group_id)][user_id]["time"] -
           time.time()) >= (5.6 * 60):
        image_data_queue[str(group_id)].pop(user_id)
        customemote.put_image_data_queue(image_data_queue)
        await custom_emote_image_set.finish("上次发图距离现在的时间太长了！请再发送图片后再使用该命令！")
    state["emote_name"] = emote_name
    state["emote_set_user_id"] = user_id
    state["confirm_save"] = False

    if matcher.get_arg("two_step_check") == None:
        is_conflict = await customemote.emote_name_is_exist(
            emote_name, group_id, user_id)
        if (is_conflict):
            nonebot.logger.debug("检测到冲突！")
        else:
            nonebot.logger.debug("没有检测到冲突！")
            matcher.set_arg("two_step_check", Message("是"))  # 不再2check
            state["confirm_save"] = True

    if (state["confirm_save"]):
        nonebot.logger.debug("可以存图！")
        await set_image(event, state["emote_name"], state["emote_set_user_id"])

async def get_at_user_id(messsage:Message)->Union[Union[str,int],None]:
        at_user_id = None
        for msg in messsage:
            if msg.type=="at":
                at_user_id = msg.data["qq"]
                break
        return at_user_id

@custom_emote_image_set.got("two_step_check", prompt="当前设置的表情名称已经存在！是否覆盖设置？")
async def _2stepcheck(bot: Bot,
                      event: GroupMessageEvent,
                      state: T_State,
                      two_step_check: Message = ArgPlainText()):
    if (two_step_check not in ["是", "否"]):
        state["max_try"] -= 1
        if (state["max_try"] < 1):
            await custom_emote_image_set.finish("输入错误次数过多，取消设置！")
        else:
            await custom_emote_image_set.reject("请发送[是/否]确认设置！")
    else:
        state["confirm_save"] = (two_step_check == "是")

    if (state["confirm_save"]):
        nonebot.logger.debug("可以存图！")
        await set_image(event, state["emote_name"], state["emote_set_user_id"])
    else:
        nonebot.logger.debug("取消存图！")
        await custom_emote_image_set.finish("取消设置！")


# @custom_emote_image_set.got("set_image")
# 所有分支里事件都结束了，直接内置处理
async def set_image(event: GroupMessageEvent, emote_name: str, emote_set_user_id:str):
    group_id: str = str(event.group_id)
    image_data_queue = await customemote.get_image_data_queue()
    execute_sucessful = False
    image_data_obj = image_data_queue[group_id][emote_set_user_id]
    try:
        execute_sucessful = await customemote.save_emote_image(
            emote_name, image_data_obj["image_file"], image_data_obj["url"],
            group_id, emote_set_user_id)
    except Exception as e:
        nonebot.logger.error("自定表情设置失败!")
        try:
            await custom_emote_image_set.finish("设置失败！出错了！")
        except Exception as e:
            pass
        raise e
    if not execute_sucessful:
        await custom_emote_image_set.finish("设置失败！出错了！")
    else:
        reply = MessageSegment.reply(
            image_data_obj["message_id"]) + MessageSegment.text("设置成功！")
        try:
            await custom_emote_image_set.send(reply)
        except Exception as e:
            nonebot.logger.error(f"回复消息发送失败！Res:{e}")
            await custom_emote_image_set.send(MessageSegment.text("设置成功！"))
        await custom_emote_image_set.finish()


# 表情记录获取Matcher
custom_emote_image_capture = on_message(priority=99, block=False)


@custom_emote_image_capture.handle()
async def _emotecap(bot: Bot, event: GroupMessageEvent, state: T_State):
    image_data_queue = await customemote.get_image_data_queue()
    group_id = event.group_id
    msg = event.get_message()
    if msg[0].type == "image":
        if not str(group_id) in image_data_queue:
            image_data_queue[f"{group_id}"] = {}
        image_data_queue[f"{group_id}"][event.get_user_id()] = {
            "image_file": msg[0].data["file"],
            "url": msg[0].data["url"],
            "user_id": event.user_id,
            "group_id": group_id,
            "message_id": event.message_id,
            "time": time.time()
        }
    return


# 表情发送Matcher
custom_emote_image_handle = on_endswith(customemote.active_keyword_tuple,
                                        priority=12,
                                        block=False)


@custom_emote_image_handle.handle()
async def _onrecallemote(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    user_id = event.get_user_id()
    msg_text = event.get_plaintext()

    for message in Message(event.get_message()):
        if message.type != "text":
            await custom_emote_image_handle.finish()

    emote_name = msg_text.strip()
    if not await customemote.send_trigger(emote_name):
        await custom_emote_image_handle.finish()

    if emote_name:
        emote_image_file, emote_save_path = await customemote.search_matcher_emote(
            emote_name, group_id, user_id)
        if emote_image_file is not None:
            try:
                data = await bot.get_image(file=emote_image_file)
            except Exception as e:
                nonebot.logger.error("自动表情包发送失败 Message Error Res:" + str(e))
                return
            image_msg = MessageSegment.image(data["url"])
        elif emote_save_path is not None:
            image_msg = MessageSegment.image(emote_save_path)
        else:
            return
        try:
            await custom_emote_image_handle.send(image_msg, timeout=30)
        except Exception as e:
            nonebot.logger.error("自动表情包发送失败 Message Send Error Res:" + str(e))
            await custom_emote_image_handle.send("图片资源失效！")
    await custom_emote_image_handle.finish()
