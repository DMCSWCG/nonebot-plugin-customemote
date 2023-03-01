import nonebot
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="群聊自定义表情包发送器",
    description="用于群聊中设置自定义表情包，并在需要的时候使用对应名称召唤机器人发送表情，不再有打开相册翻表情的烦恼",
    usage="触发方式：指令 + @user/qq/自己/图片\n发送“头像表情包”查看支持的指令",
    config=Config,
    extra={
        "unique_name": "custom_face",
        "example": "设置表情：自定义表情设置 表情名称\n[回复图片]自定表情包设置 滑稽\n召唤表情：表情名称.jpg\n傻了吧唧的.jpg",
        "author": "DMCSWCG <xxxxxxx@gmail.com>",
        "version": "0.1.0",
    },
)

