import configparser
import io
import Levenshtein as lv
import requests
from block_types import *
from dataclasses import asdict
from typing import List
from chat import create_chat_completion
import openai
from base64 import b64decode
from PIL import Image
import os
import hashlib

PROMPT = """
{"prompt":"点击角色，使角色变色 ->","completion":" \"when this sprite clicked\",\"change [color] effect by [25]\"\n"}
{"prompt":"点击角色，使角色一直旋转 ->","completion":" \"when this sprite clicked\",\"repeat [10]\",\"turn [18] degrees\"\n"}
{"prompt":"点击角色，播放音效 ->","completion":" \"when this sprite clicked\",\"play sound [Guitar Strum] until done\" \n"}
{"prompt":"点击角色，使角色跳舞 ->","completion":" \"when this sprite clicked\",\"move [10] steps\",\"play\"\n"}
{"prompt":"点击角色，改变角色尺寸 ->","completion":" \"when this sprite clicked\",\"repeat [15]\",\"change size by [10]\",\"repeat [15]\",\"change size by [-10]\"\n"}
{"prompt":"点击空格，角色旋转并改变颜色 ->","completion":" \"when [space] key pressed\",\"turn [90] degrees\",\"change [color] effect by [25]\"\n"}
{"prompt":"点击角色，使角色滑行 ->","completion":" \"when this sprite clicked\",\"glide [1] secs to x:[10],y:[100]\",\"glide [1] secs to x:[40],y:[-130]\",\"glide [1] secs to x:[10],y:[100]\"\n"}
{"prompt":"点击绿旗，使角色说话 ->","completion":" \"when green flag clicked\",\"say [Hello!] for [2] seconds\",\"say [Imagine if...] for [2] seconds\"\n"}
{"prompt":"点击空格，使角色发出声音并移动 ->","completion":" \"when [space] key pressed\",\"start sound [pop]\",\"glide [1] secs to [random position]\"\n"}
{"prompt":"按下左右键，使角色左右移动 ->","completion":" \"when [right arrow] key pressed\",\"change x by [10]\",\"when [left arrow] key pressed\",\"change x by [-10]\"\n"}
{"prompt":"按下上下键，使角色上下移动 ->","completion":" \"when [up arrow] key pressed\",\"change y by [10]\",\"when [down arrow] key pressed\",\"change y by [-10]\"\n"}
{"prompt":"点击角色，切换到下一个costume ->","completion":" \"when this sprite clicked\",\"switch costume to []\",\"wait [0.3] seconds\",\"switch costume to []\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击角色，使角色变大和变小 ->","completion":" \"when this sprite clicked\",\"repeat [2]\",\"set size to [125]%\",\"play sound [Hi Na Tabla] until done\",\"set size to [100]%\"\n"}
{"prompt":"点击绿旗，改变背景并使角色说话 ->","completion":" \"when gree flag clicked\",\"switch backdrop to [Savanna]\",\"wait [2] seconds\",\"switch backdrop to [Metro]\",\"say [Let's explore] for [2] seconds\"\n"}
{"prompt":"点击绿旗，播放声音并切换costume ->","completion":" \"when green flag clicked\",\"start sound [your recording]\",\"next costume\",\"say [] for [2] seconds\"\n"}
{"prompt":"点击绿旗，如果触碰到角色就播放声音 ->","completion":" \"when green flag clicked\",\"forever\",\"if touching [star] then\",\"play sound [Collect] until done\"\n"}
{"prompt":"点击绿旗，如果触碰到角色播放声音并增加分数 ->","completion":" \"when green flag clicked\",\"set [Score] to [0]\",\"forever\",\"if touching [star] then\",\"change [Score] by [1]\",\"play sound [Collect] until done\"\n"}
{"prompt":"点击绿旗，当分数足够切换背景 ->","completion":" \"when green flag clicked\",\"switch backdrop to []\",\"wait until (Score) == (10)\",\"switch backdrop to [Nebula]\",\"when backdrop switches to [Nebula]\",\"play sound [Win] until done\"\n"}
{"prompt":"按下空格，使角色跳起来 ->","completion":" \"when [space] key pressed\",\"change y by [60]\",\"wait [0.3] seconds\",\"change y by [-60]\"\n"}
{"prompt":"按下空格，改变角色姿势 ->","completion":" \"when [space] key pressed\",\"switch costume to [max-c]\",\"wait [0.3] seconds\",\"switch costume to [max-b]\"\n"}
{"prompt":"点击绿旗，实现角色跑步动画 ->","completion":" \"when green flag clicked\",\"go to x:[-140],y:[-60]\",\"repeat [50]\",\"move [10] steps\",\"next costume\"\n"}
{"prompt":"点击绿旗，使两个角色对话 ->","completion":" \"when green flag clicked\",\"say [I have a pet owl!] for [2] seconds\",\"wait [2] seconds\",\"when green flag clicked\",\"wait [2] seconds\",\"say [What's its name] for [2] seconds\"\n"}
{"prompt":"点击绿旗，改变背景 ->","completion":" \"when green flag clicked\",\"switch backdrop to []\",\"wait [4] seconds\",\"switch backdrop to []\"\n"}
{"prompt":"点击角色，改变颜色，播放声音 ->","completion":" “when this sprite clicked\",\"change [color] effect by [25]\",\"play sound [Magic Spell]\n"}
{"prompt":"点击绿旗，播放声音，使角色说话 ->","completion":" \"when green flag clicked\",\"start sound [recording1]\",\"say [let's go] for [2] seconds\"\n"}
{"prompt":"点击绿旗，使角色滑行 ->","completion":" “when green flag clicked\",\"go to x: [-180] y: [140]\",\"glide [1] secs to x: [-30] y: [50]\"\n"}
{"prompt":"点击绿旗，使角色走进舞台 ->","completion":" “when green flag clicked\",“hide\",\"go to x: [-240] y: [-60]\",\"show\",\"glide [2] secs to x: [0] y: [-60]\"\n"}
{"prompt":"点击绿旗，使角色说话 ->","completion":" “when green flag clicked\",“say [where are you going?] for [2] seconds\",\"broadcast [message1]\"\n"}
{"prompt":"角色收到信息，回复 ->","completion":" \"when i receive [message1]\",\"say [To the forest!] for [2] seconds\"\n"}
{"prompt":"点击绿旗，改变背景 ->","completion":" “when green flag clicked\",\"switch backdrop to [Witch House]\",\"hide\",\"wait [4] seconds\",\"switch backdrop to [Mountain]\" \n"}
{"prompt":"改变背景，使角色移动 ->","completion":" “when backdrop switches to [Mountain]\",\"go to x: [80] y: [-100]\",\"show\"\n"}
{"prompt":"点击绿旗，标线移到舞台底部，游戏结束 ->","completion":" “when green flag clicked\",\"go to x: [0] y: [-170]\",\"forever\",\"if touching [Ball] ? then\",\"stop [all]\"\n"}
{"prompt":"点击绿旗，使球在标尺上反弹，并计分 ->","completion":" “when green flag clicked\",\"forever\",\"if touching [Paddle] ? then\",“change [Score] by [1]\",\"turn clockwise pick random (170) to (190) degrees\",\"move [15] steps\",\"wait [0.5] seconds\"\n"}
{"prompt":"点击绿旗，重新设置分数 ->","completion":" “when green flag clicked\",\"set [Score] to [0]\"\n"}
{"prompt":"点击绿旗，到达目标分数，获胜 ->","completion":" “when green flag clicked\",“hide\",\"wait until [Score] = (5)\",\"show\",\"stop [all]\"\n"}
{"prompt":"点击绿旗，使角色跳舞 ->","completion":" “when green flag clicked\",“switch costume to [Ten80 top R step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top L step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top freeze]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top R cross]\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，使角色循环舞蹈动作 ->","completion":" “when green flag clicked\",“switch costume to [Ten80 stance]\",\"wait [1] seconds\",\"repeat [4]\",“switch costume to [Ten80 top R step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top L step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top freeze]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top R cross]\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，重复播放音乐 ->","completion":" “when green flag clicked\",“repeat [10]\",\"play sound [Dance Celebrate] until done\"\n"}
{"prompt":"点击绿旗，跳舞完成后说话 ->","completion":" “when green flag clicked\",“switch costume to [anina top L step]\",\"wait [0.3] seconds\",“switch costume to [anina top R step]\",\"wait [0.3] seconds\",“switch costume to [anina stance]\",\"broadcast [message1]\"\n"}
{"prompt":"角色收到信息，回复并跳舞 ->","completion":" \"when i receive [message1]\",\"say [My turn to dance!] for [1] seconds\",\"repeat [4]\",\"next costume\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，设置角色初始位置 ->","completion":" “when green flag clicked\",\"go to x: [-10] y: [20]\",\"set size to [90] %\",\"switch costume to [lb stance]\",\"show\"\n"}
{"prompt":"点击绿旗，角色变成阴影效果 ->","completion":" “when green flag clicked\",“set [brightness] effect to [-100]\",\"forever\",\"next costume\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [left arrow] key pressed\",\"switch costume to [jo pop left]\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [right arrow] key pressed\",\"switch costume to [jo pop right]\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [up arrow] key pressed\",\"switch costume to [jo top stand]\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [down arrow] key pressed\",\"switch costume to [jo pop down]\"\n"}
{"prompt":"点击绿旗，改变颜色 ->","completion":" “when green flag clicked\",\"forever\",\"change [color] effect by [25]\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，留下角色舞蹈痕迹 ->","completion":" “when green flag clicked\",\"repeat [6]\",\"pen stamp\",\"move [10] steps\",\"wait [0.1] seconds\",\"pen erase all\"\n"}
{"prompt":"点击空格键，使角色跳跃 ->","completion":" “when [space] key pressed\",\"repeat [10]\",\"change y by [10]\",“repeat [10]\",\"change y by [-10]\"\n"}
{"prompt":"点击绿旗，设置角色初始位置 ->","completion":" “when green flag clicked\",\"go to x: [-180] y: [-120]\"\n"}
{"prompt":"点击绿旗，移动障碍物 ->","completion":" “when green flag clicked\",“forever”，\"go to x: [240] y: [-145]\"，“glide [3] secs to x: [-240] y: [-145]\"\n"}
{"prompt":"点击绿旗，使角色说话 ->","completion":" “when green flag clicked\",\"go to x: [-50] y: [60]\",\"say [My name is Kiki!] for [2] seconds\"\n"}
{"prompt":"点击角色，播放音效，使角色动起来 ->","completion":" “when [space] key pressed\",“start sound [Chirp]\",\"repeat [4]\",“switch costume to [monkey-a]\",\"wait [0.2] seconds\",“switch costume to [monkey-b]\",\"wait [0.2] seconds\"\n"}
{"prompt":"点击角色，发出信息 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [food]\"\n"}
{"prompt":"点击角色，改变状态 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [drink]\",\"wait [1] seconds\",\"switch costume to [glass water-b]\",start sound [Water Drop]\",\"wait [1] seconds\",\"switch costume to [glass water-a]\"\n"}
{"prompt":"角色收到信息，进行喂水，回到原位 ->","completion":" \"when i receive [drink]\",“glide [1] secs to [Glass water]\",\"wait [1] seconds\",“glide [1] secs to x: [-50] y: [60]\"\n"}
{"prompt":"点击角色，根据不同选择，回复消息 ->","completion":" “when the sprite clicked\",\"set [Choice] to pick random (1) to (3)\",\"if (choice) = (1) then\",\"say [I like bananas!] for [2] seconds\",\"if (choice) = (2) then\",\"say [That tickles!] for [2] seconds\",\"if (choice) = (3) then\",\"say [Let's play!] for [2] seconds\"\n"}
{"prompt":"点击小球，播放音乐，并跳动 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [play]\",\"wait until touching [Monkey] ?\",\"start sound [Boing]\",\"repeat [10]\",\"change by [-5]\",\"repeat [10]\",\"change by [5]\"\n"}
{"prompt":"角色收到信息，进行玩耍，回到原位 ->","completion":" \"when i receive [play]\",“glide [1] secs to [Ball]\",\"wait [1] seconds\",“glide [1] secs to x: [-50] y: [60]\"\n"}
{"prompt":"点击绿旗，让角色到舞台顶端 ->","completion":" “when green flag clicked\",“go to [random position]\",\"set y to [180]\"\n"}
{"prompt":"点击绿旗，累计分数 ->","completion":" “when green flag clicked\",“set [Score] to [0]\",“forever”,\"if touching [Bowl] ? then\",\"play sound [pop] until done\",\"change [Score] by [1]\",\"go to [random position]\",\"set y to [180]\"\n"}
{"prompt":"点击绿旗，设置奖励分数 ->","completion":" “when green flag clicked\",“set [Score] to [0]\",“forever”,\"if touching [Bowl] ? then\",\"play sound [pop] until done\",\"change [Score] by [1]\",\"go to [random position]\",\"set y to [180]\"\n"}"""

MODEL = "gpt-3.5-turbo"


def extract_keywords(s) -> List:
    # 删除所有的","
    s = s.replace('",', '')

    # 使用""来分割字符串
    arr = s.split("\"")

    # 用于保存关键词的列表
    keywords = []

    # 遍历列表，把非空的子字符串（即关键词）存入keywords列表
    for i in arr:
        if i.strip() != '':
            keywords.append(i.strip())

    return keywords


def test():
    s = '"when green flag clicked","say [你追我啊] for [2] seconds","repeat until <touching [rabbit]>","move [10] steps","end","play sound [Boing] until done"'
    keywords = extract_keywords(s)
    print(keywords)


def cal_similarity(reply_list, blocks):
    # 计算相似度
    block_list = []
    for str in reply_list:
        if str == "end" or str == "else":
            continue
        if "wait" in str and "second" in str:
            block_list.append("control_wait")
            continue
        if "if" in str:
            block_list.append("control_if_else")
            continue
        similarity, max_similarity = 0, 0
        temp_block = ""
        for value in asdict(blocks).values():
            similarity = [lv.ratio(str, v) for v in value]
            max_value = max(similarity)
            max_index = similarity.index(max_value)
            block_by_index = list(value.items())[max_index][1]
            # similarity = lv.ratio(str, value)
            if max_value > max_similarity:
                max_similarity = max_value
                temp_block = block_by_index
                # print('Similarity is', max_similarity, value)
        block_list.append(temp_block)
    return block_list


def init_code_agent():
    pass


def question_and_relpy(question):
    messages = []
    messages.append({"role": "user", "content": question})
    agent_reply = create_chat_completion(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    # messages.append({"role": "assistant", "content": agent_reply})
    return agent_reply

def generate_draw(drawing_type, drawing_content, save_path):
    temp_memory = []
    if drawing_type == "role":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。你的工作是提供简短的一句话描述。这里有一个关于动画风格角色的描述<{drawing_content}>。使用类似英文生成提示："Anime-style human with a transparent background, exploring a magical world with a butterfly companion. Line art, anime, colored, child style."。翻译为英语。
        """
        })
    elif drawing_type == "background":
        temp_memory.append({
            "role":
            "user",
            "content":
            f"""你是人工智能程序的提示生成器。你的工作是提供简短的一句话描述。这里有一个关于动画风格背景的描述<{drawing_content}>，你需要根据<描述>决定：场景发生的地方，重点的景物。使用类似英文生成提示："Forest with running track at the end, featuring trees and a running track. Line art, anime, colored, child style."。翻译为英语。
        """
        })
    else:
        raise "Not valid drawing type"
    # print(temp_memory)
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=temp_memory,
                                         temperature=0)
    print("agent: ", agent_reply)
    image_data = generate_draw_with_dalle(agent_reply, save_path)
    return image_data

def generate_draw_with_dalle(prompt, save_path):
    # image_data_list = []
    response = openai.Image.create(prompt=prompt,
                                   n=1,
                                   size="256x256",
                                   response_format="b64_json")
    for index, image_dict in enumerate(response["data"]):
        image_data_return = image_dict["b64_json"]
        # image_data_list.append(image_data)
        with open(f"{save_path}.png", mode="wb") as png:
            png.write(b64decode(image_dict["b64_json"]))
    return image_data_return


def get_auth_from_stability():
    url = f"https://api.stability.ai/v1/user/account"
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    api_key = conf.get("stability", "api")
    response = requests.get(url,
                            headers={"Authorization": f"Bearer {api_key}"})
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))
    payload = response.json()


def generate_draw_with_stable(prompt, save_path):
    engine_id = "stable-diffusion-v1-5"
    api_host = 'https://api.stability.ai'
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    api_key = conf.get("stability", "api")
    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [{
                "text": prompt
            }],
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "height": 512,
            "width": 512,
            "samples": 1,
            "steps": 30,
        },
    )
    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    for i, image in enumerate(data["artifacts"]):
        image_data = image["base64"]
        with open(f"{save_path}.png", "wb") as f:
            f.write(b64decode(image["base64"]))
    return image_data


def generate_image_to_image(prompt, base_image):
    image = Image.open(base_image)
    resized_image = image.resize((512, 512))
    with io.BytesIO() as buffer:
        resized_image.save(buffer, format='PNG')
        binary_data = buffer.getvalue()
    engine_id = "stable-diffusion-v1-5"
    api_host = 'https://api.stability.ai'
    conf = configparser.ConfigParser()
    conf.read("./envs/keys.ini")
    api_key = conf.get("stability", "api")
    if api_key is None:
        raise Exception("Missing Stability API key.")

    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/image-to-image",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        files={"init_image": binary_data},
        data={
            "image_strength": 0.35,
            "init_image_mode": "IMAGE_STRENGTH",
            "text_prompts[0][text]": prompt,
            "cfg_scale": 7,
            "clip_guidance_preset": "FAST_BLUE",
            "samples": 1,
            "steps": 30,
        })

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    for i, image in enumerate(data["artifacts"]):
        image_data = image["base64"]
        # only for test
        with open("test.png", "wb") as f:
            f.write(b64decode(image["base64"]))
    return image_data


def split_to_parts(reply: str):
    lines = reply.split('\n')
    reply_list = []
    for line in lines:
        if line.strip():
            story = line.split('.', 1)[-1]  # 去掉编号部分
            reply_list.append(story)

    return reply_list
    # print(lines[0])
    # result = []
    # for line in lines:
    #     parts = line.split('：')
    #     # 去掉编号部分
    #     if len(parts) == 2:
    #         parts[0] = parts[0].split('. ')[-1]
    #     result.append(parts)

    # # print(result)
    # return result

def toSVG(infile):
    image = Image.open(infile).convert('RGBA')
    data = image.load()
    width, height = image.size
    svg_str = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg_str += '<svg id="svg2" xmlns="http://www.w3.org/2000/svg" version="1.1" \
                width="%(x)i" height="%(y)i" viewBox="0 0 %(x)i %(y)i">\n' % \
              {'x': width, 'y': height}
    for y in range(height):
        for x in range(width):
            rgba = data[x, y]
            rgb = '#%02x%02x%02x' % rgba[:3]
            if rgba[3] > 0:
                svg_str += '<rect width="1" height="1" x="%i" y="%i" fill="%s" \
                    fill-opacity="%.2f" />\n' % (x, y, rgb, rgba[3]/255.0)
    svg_str += '</svg>\n'
    return svg_str

# 计算字符串的MD5哈希值的函数
def get_str_md5(input_str):
    md5_obj = hashlib.md5()
    md5_obj.update(input_str.encode())
    return md5_obj.hexdigest()


def generate_js():
    backdrop_files = os.listdir('static/scene')
    costume_files = os.listdir('static/role')
   
    with open('C:/Users/11488/Desktop/react_try/scratch-gui/src/lib/default-project/index.js', 'w') as f:
        f.write('import projectData from \'./project-data\';\n')
        for i, file in enumerate(backdrop_files):
            f.write('import backdrop' + str(i + 1) + ' from \'!raw-loader!./' + file + '\';\n')
        for i, file in enumerate(costume_files):
            f.write('import costume' + str(i + 1) + ' from \'!raw-loader!./' + file + '\';\n')

        f.write('\nconst defaultProject = translator => {\n')
        f.write('let _TextEncoder;\n')
        f.write('if (typeof TextEncoder === \'undefined\') {\n')
        f.write('    _TextEncoder = require(\'text-encoding\').TextEncoder;\n')
        f.write('} else {\n')
        f.write('    _TextEncoder = TextEncoder;\n')
        f.write('}\n')
        f.write('const encoder = new _TextEncoder();\n\n')
        f.write('const projectJson = projectData(translator);\n\n')
        f.write('    return [{\n')
        f.write('        id: 0,\n')
        f.write('        assetType: \'Project\',\n')
        f.write('        dataFormat: \'JSON\',\n')
        f.write('        data: JSON.stringify(projectJson)\n')
        f.write('    },\n')

        for i, file in enumerate(backdrop_files):
            f.write('    {\n')
            f.write('        id: \'' + file.split('.')[0] + '\',\n')
            f.write('        assetType: \'ImageVector\',\n')
            f.write('        dataFormat: \'SVG\',\n')
            f.write('        data: encoder.encode(backdrop' + str(i + 1) + ')\n')
            f.write('    },\n')
        
        for i, file in enumerate(costume_files):
            f.write('    {\n')
            f.write('        id: \'' + file.split('.')[0] + '\',\n')
            f.write('        assetType: \'ImageVector\',\n')
            f.write('        dataFormat: \'SVG\',\n')
            f.write('        data: encoder.encode(costume' + str(i + 1) + ')\n')
            f.write('    },\n')

        f.write('];\n};\n\nexport default defaultProject;\n')
        
        
def generate_js_project():
    backdrop_files = os.listdir('static/scene')
    costume_files = os.listdir('static/role')

    with open('C:/Users/11488/Desktop/react_try/scratch-gui/src/lib/default-project/project-data.js', 'w') as f:
        f.write('import {defineMessages} from \'react-intl\';\n')
        f.write('import sharedMessages from \'../shared-messages\';\n\n')
        f.write('let messages = defineMessages({\n')
        f.write('    meow: {\n')
        f.write('        defaultMessage: \'Meow\',\n')
        f.write('        description: \'Name for the meow sound\',\n')
        f.write('        id: \'gui.defaultProject.meow\'\n')
        f.write('    },\n')
        f.write('    variable: {\n')
        f.write('        defaultMessage: \'my variable\',\n')
        f.write('        description: \'Name for the default variable\',\n')
        f.write('        id: \'gui.defaultProject.variable\'\n')
        f.write('    }\n')
        f.write('});\n\n')
        f.write('messages = {...messages, ...sharedMessages};\n\n')
        f.write('const defaultTranslator = msgObj => msgObj.defaultMessage;\n\n')
        
        f.write('/**\n')
        f.write(' * Generates the project data.\n')
        f.write(' * @param {function} translateFunction - A function to translate the text in the project.\n')
        f.write(' * @return {object} The project data with multiple targets each with its own properties.\n')
        f.write(' */\n')
        
        f.write('const projectData = translateFunction => {\n')
        f.write('    const translator = translateFunction || defaultTranslator;\n')
        f.write('    return ({\n')
        f.write('        targets: [\n')

        # for i, file in enumerate(backdrop_files):
        f.write('            {\n')
        f.write('                isStage: true,\n')
        f.write('                name: \'Stage\',\n')
        f.write('                variables: {\n')
        f.write('                    \'`jEk@4|i[#Fk?(8x)AV.-my variable\': [\n')
        f.write('                        translator(messages.variable),\n')
        f.write('                        0\n')
        f.write('                    ]\n')
        f.write('                },\n')
        f.write('                lists: {},\n')
        f.write('                broadcasts: {},\n')
        f.write('                blocks: {},\n')
        f.write('                currentCostume: 0,\n')
        f.write('                costumes: [\n')
        for i, file in enumerate(backdrop_files):
            f.write('                    {\n')
            f.write('                        assetId: \'' + file.split('.')[0] + '\',\n')
            f.write('                        name: translator(messages.backdrop, {index: ' + str(i+1) + '}),\n')
            f.write('                        md5ext: \'' + file + '\',\n')
            f.write('                        dataFormat: \'svg\',\n')
            f.write('                        rotationCenterX: 500,\n')
            f.write('                        rotationCenterY: 460\n')
            f.write('                    },\n')
        f.write('                ],\n')
        f.write('                sounds: [],\n')
        f.write('                volume: 100\n')
        f.write('            },\n')
        for i, file in enumerate(costume_files):
            f.write('            {\n')
            f.write('                isStage: false,\n')
            f.write('                name: translator(messages.sprite, {index: ' + str(i + 1) + '}),\n')
            f.write('                variables: {},\n')
            f.write('                lists: {},\n')
            f.write('                broadcasts: {},\n')
            f.write('                blocks: {},\n')
            f.write('                currentCostume: 0,\n')
            f.write('                costumes: [\n')
        
            f.write('                    {\n')
            f.write('                        assetId: \'' + file.split('.')[0] + '\',\n')
            f.write('                        name: translator(messages.costume, {index: ' + str(1) + '}),\n')
            f.write('                        bitmapResolution: 1,\n')
            f.write('                        md5ext: \'' + file + '\',\n')
            f.write('                        dataFormat: \'svg\',\n')
            f.write('                        rotationCenterX: 500,\n')
            f.write('                        rotationCenterY: 460\n')
            f.write('                    },\n')
            f.write('                ],\n')
            f.write('                sounds: [],\n')
            f.write('                volume: 100,\n')
            f.write('                visible: true,\n')
            f.write('                x: 0,\n')
            f.write('                y: 0,\n')
            f.write('                size: 100,\n')
            f.write('                direction: 90,\n')
            f.write('                draggable: false,\n')
            f.write('                rotationStyle: \'all around\'\n')
            f.write('            },\n')

        f.write('        ],\n')
        f.write('        meta: {\n')
        f.write('            semver: \'3.0.0\',\n')
        f.write('            vm: \'0.1.0\',\n')
        f.write('            agent: \'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36\'\n')
        f.write('        }\n')
        f.write('    });\n')
        f.write('};\n\n')
        f.write('export default projectData;\n')

def test():
    string = '1. 小明：一个勇敢的男孩，喜欢探险和冒险。他在森林里迷路了，正在寻找回家的路。\n2. 小芳：一个聪明的女孩，喜欢读书和学习。她在图书馆里发现了一本神秘的书，决定破解其中的谜题。\n3. 小华：一个善良的男孩，喜欢帮助别人。他在街上看到一个老奶奶摔倒了，决定去帮助她。\n4. 小玲：一个有想象力的女孩，喜欢画画和创作。她在花园里发现了一只神奇的小鸟，决定和它成为朋友。'
    c = split_to_parts(string)
    print(c)
    # print(c[0][0])
    # print(c[0][1])


if __name__ == "__main__":
    generate_image_to_image("a blue star with magical sky",
                            base_image=r"C:\Users\YunNong\Desktop\star.png")
    # generate_draw_with_dalle("Forest with running track at the end, featuring trees and a running track. Line art, anime, colored, child style.", "2-b")
    # generate_draw_with_stable(
    #     "Anime-style human, in line art with a transparent background, exploring a magical world with a butterfly companion.",
    #     "1")
    # test()
    exit(0)
    agent_reply = '"when green flag clicked","say [你追我啊] for [2] seconds","repeat until <touching [rabbit]>","move [10] steps","end","play sound [Boing] until done"'
    extracted_reply = extract_keywords(agent_reply)
    print(extracted_reply)
    motion_blocks = MotionBlocks()
    looks_blocks = LooksBlocks()
    sound_blocks = SoundBlocks()
    events_blocks = EventsBlocks()
    control_blocks = ControlBlocks()
    sensing_blocks = SensingBlocks()
    ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                               events_blocks, control_blocks, sensing_blocks)
    block_list = cal_similarity(extracted_reply, ass_block)
    print(block_list)