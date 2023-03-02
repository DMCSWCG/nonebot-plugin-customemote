import os
import nonebot

try:
    import ujson as json
except:
    import json

from difflib import SequenceMatcher
import aiofiles
import httpx
from nonebot import get_driver
from pathlib import Path
import imghdr,random
from string import ascii_letters
from .config import Config


class CustomEmote:
    def __init__(self,setup_config:Config) -> None:
        save_emote_path = setup_config.save_emote_path
        save_emote_mode = setup_config.save_emote_mode
        if abs(save_emote_mode)>1:
            nonebot.logger.warning(f"Emote save mode {save_emote_mode} not supported! Will use message id mode(0) to save emote data!")
            save_emote_mode = 0
        self.save_emote_path = Path(os.path.abspath(save_emote_path))
        self.group_image_path  = Path(self.save_emote_path,"group")
        self.group_image_save_path = Path(self.save_emote_path,"image")
        self.temp_image_path   = Path(self.save_emote_path,"temp")
        self.emote_save_mode = save_emote_mode
        self.active_keyword  = ["jpg","png","gif","JPG","PNG","GIF"]
        self.image_data_queue = {}
        self.log_map()
        self.check_data_path()

    def log_map(self):
        self.error = nonebot.logger.error
        self.warning = nonebot.logger.warning
        self.info = nonebot.logger.info
        self.debug = nonebot.logger.debug
    
    async def get_image_data_queue(self)->dict:
        return self.image_data_queue
    
    async def put_image_data_queue(self,queue:dict)->bool:
        if not isinstance(queue,dict):
            return False
        self.image_data_queue = queue
        return True

    def check_data_path(self):
        if not os.path.exists(self.save_emote_path):
            os.makedirs(self.save_emote_path)
        if not os.path.exists(self.group_image_path):
            os.makedirs(self.group_image_path)
        if not os.path.exists(self.temp_image_path):
            os.makedirs(self.temp_image_path)
        if not os.path.exists(self.group_image_save_path):
            os.makedirs(self.group_image_save_path)
    
    async def send_trigger(self,text:str):
        for keyword in self.active_keyword:
            if text.endswith(keyword):
                return True
        return False
    
    async def get_emote_name(self,text:str)->str:
        emote_name = text.replace(".","")
        for not_in_str in self.active_keyword:
            emote_name = emote_name.replace(not_in_str,"")
        return emote_name
    
    async def ReadJson(self,path):
        async with aiofiles.open(path,"r") as f:
            data = await f.readlines()
        return json.loads("".join(data))
    
    async def WriteJson(self,path,data):
        async with aiofiles.open(path,"w+") as f:
            await f.write(json.dumps(data))

    async def download_image(self,url):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                data = await client.get(url)
            prepare_name = "".join(random.choices(ascii_letters,12))+str(random.randint(10E5,10E6))
            save_path = Path(self.temp_image_path,prepare_name)
            async with aiofiles.open(save_path,"wb") as f:
                await f.write(data)
            return save_path
        except Exception as e:
            self.error("表情图片下载失败 Res:{}".format(e))
            return None
        
    async def save_as_cqhttp_image_file(self,emote_name,file,group_id,user_id,share=True) -> dict:
        data_path = Path(self.group_image_path,f"{group_id}.json")
        if os.path.exists(data_path):
            data = await self.ReadJson(data_path)
            data[emote_name]["image_file"]=file
            data[emote_name]["user_id"]=user_id
            data[emote_name]["share"]=share
        else:
            data = {}
            data[emote_name]={"image_file":file,"image_path":None,"user_id":user_id,"share":share}
        return data
    
    async def save_as_direct_image_file(self,emote_name,url,group_id,user_id,share=True) -> dict:
        async def to_save(save_path):
            path_head = "file:///"
            data_path = Path(self.group_image_path,f"{group_id}.json")
            data = {}
            if os.path.exists(save_path):
                data = await self.ReadJson(data_path)
                data[emote_name]["image_path"]=save_path
                data[emote_name]["user_id"]=user_id
                data[emote_name]["share"]=share
            else:
                data = {}
                data[emote_name]={"image_file":None,"image_path":path_head+save_path,"user_id":user_id,"share":share}
            return data

        save_path = await self.download_image(url)
        if save_path is None:
            self.error("图片下载失败！")
            return {}
        image_type = imghdr.what(save_path)
        if not image_type:
            self.error("不支持的图片格式！")
            os.remove(save_path)
            return {}
        else:
            save_path_final = Path(self.group_image_save_path,group_id,emote_name+".{}".format(image_type))
            async with aiofiles.open(save_path,"rb") as f:
                data = await f.read()
            async with aiofiles.open(save_path_final,"wb") as f:
                await f.write(data)
            os.remove(save_path)
        return await to_save(save_path_final)

    async def emote_name_is_exist(self,emote_name:str,group_id, user_id) -> bool:
        file,url = await self.search_matcher_emote(emote_name,group_id, user_id)
        if file is not None or url is not None:
            return True
        return False
    
    async def save_emote_image(self,emote_name=None,file=None,url=None,group_id=None,user_id=None,share=True) -> bool:
        data = {}
        if self.emote_save_mode == 0:
            data = await self.save_as_cqhttp_image_file(emote_name=emote_name,file=file,group_id=group_id,user_id=user_id,share=share)
        elif self.emote_save_mode == 1:
            data = await self.save_as_direct_image_file(emote_name=emote_name,url=url,group_id=group_id,user_id=user_id,share=share)
        else:
            self.error("图片存储模式设置错误！")
            return
        if data is {}:
            return False
        data_path = Path(self.group_image_path,f"{group_id}.json")
        self.info(f"Saving images to {data_path}")
        await self.WriteJson(data_path,data)
        return True
        
    async def get_image_file_list(self,group_id):
        data_path = Path(self.group_image_path,f"{group_id}.json")
        if os.path.exists(data_path):
            group_self_data = await self.ReadJson(data_path)
        else:
            group_self_data = None
        return group_self_data
    
    async def get_best_matcher_file(self,image_data,emote_name):
        for data in image_data.keys():
            MatcherRate = SequenceMatcher(None, data, emote_name).ratio()
            if MatcherRate>0.85:
                return image_data[data]
        return None

    async def search_matcher_emote(self,emote_name,group_id,user_id):
        emote_name = await self.get_emote_name(emote_name)
        self_group_data = await self.get_image_file_list(group_id)
        if self_group_data is None:
            return None,None
        emote_data = await self.get_best_matcher_file(self_group_data,emote_name)
        # NONE CHECK
        if emote_data is None:
            return None,None
        if not emote_data["share"] and str(emote_data["user_id"])!=str(user_id):
            return None,None
        return emote_data["image_file"], emote_data["image_path"]

    async def remove_custom_emote(self,group_id,keyword):
        data_path = Path(self.group_image_path+f"{group_id}.json")
        if os.path.exists(data_path):
            data = await self.ReadJson(data_path)
            if keyword not in data:
                return False
            data.pop(keyword)
            await self.WriteJson(data_path)
            return True
        return False
