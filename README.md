<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>
<div align="center">

  # Custom Emote
  ✨ 基于[NoneBot2](https://github.com/nonebot/nonebot2)的插件，群聊自定义表情包发送器 ✨
  </br>
  ✨ Custom Emote ✨
</div>

## 功能介绍

用于群聊中设置自定义的表情包,不再有翻相册的烦恼。

只需要发送 *.jpg 或 *.png 或 *.gif 机器人就会发送设置好的表情图片

## 用法简介


### 全局配置：

```python
save_face_path = "" # 表情包数据存放位置 默认./data/custom_face_data/

save_face_mode = 0  # 表情包的保存模式 
# 0 为使用cqhttp image file保存模式,使用Go-cqhttp的图像记录文件,存在失效的问题,优点是节约硬盘空间

# 1 为图片文件下载保存模式,直接下载图像文件保存在服务器上,无失效问题(如文件被删除则失效),但需注意存储空间使用量
```
### 指令:

#### 1、"自定表情包设置", "自定义表情包设置", "自定表情设置", "自定义表情设置" 

用于设置表情图片，图片来源你或者其他人发送的图片，为最近一次发送的图片。  

#### 2、*.jpg、*.png、*.gif 

召唤指令，*为你设置的表情包名称，使用相似度判断触发。可能有意想不到的效果。  


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
