import os
import nonebot
import ujson as json
from difflib import SequenceMatcher
import aiofiles
import httpx
from nonebot import get_driver
from pathlib import Path
import imghdr,random
from string import ascii_letters

save_face_path = "./data/custom_face_data/"
try:
    save_face_path = get_driver().config.save_face_path
except:
    save_face_path = "./data/custom_face_data/"
save_face_mode = 0
try:
    save_face_mode = abs(int(get_driver().config.save_face_path)) # message id mode set 0 photo mode set 1
except:
    save_face_mode = 0
if abs(save_face_mode)>1:
    nonebot.logger.warning("Not support face save mode! Will use message id mode to save face data!")
    save_face_mode = 0

class CustomFace:
    def __init__(self) -> None:
        self.save_face_path = Path(os.path.abspath(save_face_path))
        self.group_image_path  = Path(self.save_face_path,"group")
        self.group_image_save_path = Path(self.save_face_path,"image")
        self.temp_image_path   = Path(self.save_face_path,"temp")
        self.face_save_mode = save_face_mode
        self.log_map()

    def log_map(self):
        self.error = nonebot.logger.error
        self.warning = nonebot.logger.warning
        self.info = nonebot.logger.info
    
    def check_data_path(self):
        if not os.path.exists(self,self.save_face_path):
            os.makedirs(self.save_face_path)
        if not os.path.exists(self.group_image_path):
            os.makedirs(self.group_image_path)
        if not os.path.exists(self.temp_image_path):
            os.makedirs(self.temp_image_path)
        if not os.path.exists(self.group_image_save_path):
            os.makedirs(self.group_image_save_path)
    
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
        
    async def save_as_message_id(self,face_name,group_id,file) -> dict:
        data_path = Path(self.group_image_path,f"/{group_id}.json")
        if os.path.exists(data_path):
            data = await self.ReadJson(data_path)
            data[face_name]["message_id"]=file
        else:
            data = {}
            data[face_name]={"message_id":file,"photo_path":None}
        return data
    
    async def save_as_photo_file(self,face_name,group_id,url) -> dict:
        async def to_save(save_path):
            path_head = "file:///"
            data_path = Path(self.group_image_path,f"/{group_id}.json")
            data = {}
            if os.path.exists(save_path):
                data = await self.ReadJson(data_path)
                data[face_name]["photo_path"]=save_path
            else:
                data = {}
                data[face_name]={"message_id":None,"photo_path":path_head+save_path}
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
            save_path_final = Path(self.group_image_save_path,group_id,face_name+".{}".format(image_type))
            async with aiofiles.open(save_path,"rb") as f:
                data = await f.read()
            async with aiofiles.open(save_path_final,"wb") as f:
                await f.write(data)
            os.remove(save_path)
        return await to_save(save_path_final)

        

    async def save_image_file(self,face_name=None,file=None,url=None,group_id=None) -> bool:
        data = {}
        if self.face_save_mode == 0:
            data = await self.save_as_message_id(face_name=face_name,file=file,group_id=group_id)
        elif self.face_save_mode == 1:
            data = await self.save_as_photo_file(face_name=face_name,group_id=group_id,url=url)
        else:
            self.error("图片存储模式设置错误！")
            return
        if data is {}:
            return False
        data_path = Path(self.group_image_path,f"/{group_id}.json")
        await self.WriteJson(data_path,data)
        return True
        

    async def get_image_file_list(self,group_id):
        data_path = Path(self.group_image_path,f"/{group_id}.json")
        if os.path.exists(data_path):
            group_self_data = await self.ReadJson(data_path)
        else:
            group_self_data = None
        return group_self_data
    
    async def get_best_matcher_file(self,image_data,face_name):
        for data in image_data.keys():
            MatcherRate = SequenceMatcher(None, data, face_name).ratio()
            if MatcherRate>0.85:
                return image_data[data]
        return None

    async def search_matcher_face(self,face_name,group_id):
        self_group_data = await self.get_image_file_list(group_id)
        if self_group_data is None:
            return None
        face_data = await self.get_best_matcher_file(self_group_data,face_name)
        return face_data["message_id"] , face_data["photo_path"]

    async def remove_custom_face(self,group_id,keyword):
        if os.path.exists(self.group_image_path+f"/{group_id}.json"):
            data = await self.ReadJson(self.group_image_path+f"/{group_id}.json")
            if keyword not in data:
                return None
            data.pop(keyword)
            await self.WriteJson(self.group_image_path+f"/{group_id}.json",data)
            return True
        return False