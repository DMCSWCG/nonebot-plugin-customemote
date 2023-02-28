<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>
<div align="center">

  # Custom Face
  ✨ 基于[NoneBot](https://github.com/nonebot/nonebot2)的插件，群聊自定义表情包发送器 ✨
  </br>
  ✨ Custom Face ✨
</div>

## 功能介绍

用于群聊中设置自定义的表情包,不再有翻相册的烦恼。

只需要发送 *.jpg 或 *.png 或 *.gif 机器人就会自动发送设置好的表情包

当前仅支持 nonebot 2.0.0a16 ！

## 用法简介


全局配置：

```python
save_face_path = "" # 表情包数据存放位置 默认./data/custom_face_data/

save_face_mode = 0  # 表情包的保存模式 
# 0 为message_id保存模式,存在失效的问题,优点是节约硬盘空间 

# 1 为文件保存模式,直接下载在服务器上,需注意存储空间使用量
```

按常规方法导入插件即可。多群控制开关没有做,自己加一下吧（懒）

<a href="https://github.com/Utmost-Happiness-Planet/uhpstatus/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-orange" alt="license">
  </a>
  
  <a href="https://github.com/nonebot/nonebot2">
    <img src="https://img.shields.io/badge/nonebot-v2-red" alt="nonebot">
  </a> 
  
  <a href="">
    <img src="https://img.shields.io/badge/release-v1.0-blueviolet" alt="release">
</a>
