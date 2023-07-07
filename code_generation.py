import json
from typing import List
import Levenshtein as lv
import xml.etree.ElementTree as ET
from dataclasses import asdict
from block_types import *
import re
from chat import create_chat_completion

PROMPT2 = """
1. {"prompt":"Sprite说话 ->","completion":" \"when green flag clicked\",\"say [Hello!] for [2] seconds\",\"say [Imagine if...] for [2] seconds\"\n"}
2. {"prompt":"点击Sprite，使Sprite变大和变小 ->","completion":" \"when this sprite clicked\",\"repeat [2]\",\"set size to [125]%\",\"play sound [Hi Na Tabla] until done\",\"set size to [100]%\"\n"}
3. {"prompt":"按下左右键，使Sprite左右移动 ->","completion":" \"when [right arrow] key pressed\",\"change x by [10]\",\"when [left arrow] key pressed\",\"change x by [-10]\"\n"}
4. {"prompt":"小猫和小狗对话 ->","completion":"Cat:\"when green flag clicked\",\"say [Hello!] for [2] seconds\",\"broadcast [message1]\"\nDog:\"when I recieve [massage1]\",\"wait [2] seconds\",\"say [Hello!] for [2] seconds\"\n"}
5. {"prompt":"Sprite A和Sprite B赛跑 ->","completion":"Sprite A:\"when green flag clicked\",\"forever\",\"control_repeat[10]\",\"move [10] steps\",\"event_broadcast[message1]andwait\"\nSprite B:\"when I recieve [massage1]\",\"control_repeat[10]\",\"move [5] steps\"\n"}
"""
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

def chatgpt_extract_code(text):
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""提取<文本>中包含的code：<{text}>，并以json形式输出，其中包含以下key:code"""
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    print(agent_reply)
    agent_reply = json.loads(agent_reply)["code"]
    if isinstance(agent_reply, list):
        return agent_reply
    elif isinstance(agent_reply, str):
        return agent_reply.splitlines()
    else:
        return f"Not valid:{type(agent_reply)}, please check the content" 
    
def extract_code(text):
    code_blocks = re.findall(r"```([^`]+)```", text, re.DOTALL)
    extracted_code = []
    
    for code_block in code_blocks:
        lines = code_block.strip('`').split('\n')
        for line in lines:
            if line.strip() and not line.strip().startswith('#'):
                extracted_code.append(line.strip())
    
    return extracted_code

def extract_keywords(s) -> List:
    code_lines = extract_code(s)
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


def generate_code_step(content):
    '''
    使用哪些模块（Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables）
    运动、外观、声音、事件、控制、侦测、运算、变量
    '''
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""你是一个专业的Scratch编程老师。当我询问你如何实现一个Scratch功能的时候，你需要分两步告诉我：
        步骤1：使用哪些模块（Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables）
        步骤2：使用Scratch3.0中的代码块，按照尖括号内的代码的风格：<{PROMPT}>。回答问题，请补充completion["prompt":{content} ->,"completion":]"""
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    return agent_reply

def extract_step(input_text):
    # 查找步骤1的位置
    step1_index = input_text.find("步骤1")
    step2_index = input_text.find("步骤2")
    if step1_index != -1:
        # 提取步骤1后面的内容
        step1_content = input_text[step1_index + len("步骤1") + 1:]
        step2_index_1 = step1_content.find("步骤2")
        if step2_index_1 != -1:
            # 如果找到步骤2，则截取步骤1后面到步骤2之间的内容
            step1_content = step1_content[:step2_index_1]
        # 去除换行符和空格
        step1_content = step1_content.strip()
        # 查找步骤2的位置
    if step2_index != -1:
        # 提取步骤2后面的内容
        step2_content = input_text[step2_index + len("步骤2") + 1:]
        # 去除换行符和空格
        step2_content = step2_content.strip()
    return step1_content, step2_content

def main():
    motion_blocks = MotionBlocks()
    looks_blocks = LooksBlocks()
    sound_blocks = SoundBlocks()
    events_blocks = EventsBlocks()
    control_blocks = ControlBlocks()
    sensing_blocks = SensingBlocks()
    ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                            events_blocks, control_blocks, sensing_blocks)
    # 角色状态（单一角色），对话（事件、控制）（两个角色、三个角色）
    content = generate_code_step("使用键盘控制角色移动")
    print(content)
    r1, step2 = extract_step(content)
    print("step1:", r1)
    print(step2)
    extracted_reply = chatgpt_extract_code(step2)
    print("extracted_reply:\n", extracted_reply)
    block_list = cal_similarity(extracted_reply, ass_block)
    block_list = [block for block in block_list if block]
    print("block_list:\n", block_list)

# main()
# print("r1", r1, "\nr2", r2)
