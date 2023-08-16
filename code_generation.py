import json
from typing import List
import Levenshtein as lv
from dataclasses import asdict
from block_types import *
import re
from chat import create_chat_completion
from tools import MODEL
PROMPT2 = """
{"prompt":"点击绿旗，使角色说话 ->","completion":" \"when green flag clicked\",\"say [Hello!] for [2] seconds\",\"say [Imagine if...] for [2] seconds\"\n"}
"""
PROMPT = """
{"prompt":"点击角色，切换到下一个costume ->","completion":" \"when this sprite clicked\",\"switch costume to []\",\"wait [0.3] seconds\",\"switch costume to []\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，改变背景并使角色说话 ->","completion":" \"when gree flag clicked\",\"switch backdrop to [Savanna]\",\"wait [2] seconds\",\"switch backdrop to [Metro]\",\"say [Let's explore] for [2] seconds\"\n"}
{"prompt":"点击绿旗，如果触碰到角色就播放声音 ->","completion":" \"when green flag clicked\",\"forever\",\"if touching [star] then\",\"play sound [Collect] until done\"\n"}
{"prompt":"点击绿旗，如果触碰到角色播放声音并增加分数 ->","completion":" \"when green flag clicked\",\"set [Score] to [0]\",\"forever\",\"if touching [star] then\",\"change [Score] by [1]\",\"play sound [Collect] until done\"\n"}
{"prompt":"点击绿旗，当分数足够切换背景 ->","completion":" \"when green flag clicked\",\"switch backdrop to []\",\"wait until (Score) == (10)\",\"switch backdrop to [Nebula]\",\"when backdrop switches to [Nebula]\",\"play sound [Win] until done\"\n"}
{"prompt":"按下空格，使角色跳起来 ->","completion":" \"when [space] key pressed\",\"change y by [60]\",\"wait [0.3] seconds\",\"change y by [-60]\"\n"}
{"prompt":"按下空格，改变角色姿势 ->","completion":" \"when [space] key pressed\",\"switch costume to [max-c]\",\"wait [0.3] seconds\",\"switch costume to [max-b]\"\n"}
{"prompt":"点击绿旗，实现角色跑步动画 ->","completion":" \"when green flag clicked\",\"go to x:[-140],y:[-60]\",\"repeat [50]\",\"move [10] steps\",\"next costume\"\n"}
{"prompt":"点击绿旗，使两个角色对话 ->","completion":" \"when green flag clicked\",\"say [I have a pet owl!] for [2] seconds\",\"wait [2] seconds\",\"when green flag clicked\",\"wait [2] seconds\",\"say [What's its name] for [2] seconds\"\n"}
{"prompt":"点击角色，改变颜色，播放声音 ->","completion":" “when this sprite clicked\",\"change [color] effect by [25]\",\"play sound [Magic Spell]\n"}
{"prompt":"点击绿旗，播放声音，使角色说话 ->","completion":" \"when green flag clicked\",\"start sound [recording1]\",\"say [let's go] for [2] seconds\"\n"}
{"prompt":"点击绿旗，使角色滑行 ->","completion":" “when green flag clicked\",\"go to x: [-180] y: [140]\",\"glide [1] secs to x: [-30] y: [50]\"\n"}
{"prompt":"点击绿旗，使角色走进舞台 ->","completion":" “when green flag clicked\",“hide\",\"go to x: [-240] y: [-60]\",\"show\",\"glide [2] secs to x: [0] y: [-60]\"\n"}
{"prompt":"角色收到信息，回复 ->","completion":" \"when i receive [message1]\",\"say [To the forest!] for [2] seconds\"\n"}
{"prompt":"点击绿旗，改变背景 ->","completion":" “when green flag clicked\",\"switch backdrop to [Witch House]\",\"hide\",\"wait [4] seconds\",\"switch backdrop to [Mountain]\" \n"}
{"prompt":"改变背景，使角色移动 ->","completion":" “when backdrop switches to [Mountain]\",\"go to x: [80] y: [-100]\",\"show\"\n"}
{"prompt":"点击绿旗，使角色跳舞 ->","completion":" “when green flag clicked\",“switch costume to [Ten80 top R step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top L step]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top freeze]\",\"wait [0.3] seconds\",“switch costume to [Ten80 top R cross]\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，重复播放音乐 ->","completion":" “when green flag clicked\",“repeat [10]\",\"play sound [Dance Celebrate] until done\"\n"}
{"prompt":"点击绿旗，跳舞完成后说话 ->","completion":" “when green flag clicked\",“switch costume to [anina top L step]\",\"wait [0.3] seconds\",“switch costume to [anina top R step]\",\"wait [0.3] seconds\",“switch costume to [anina stance]\",\"broadcast [message1]\"\n"}
{"prompt":"角色收到信息，回复并跳舞 ->","completion":" \"when i receive [message1]\",\"say [My turn to dance!] for [1] seconds\",\"repeat [4]\",\"next costume\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击绿旗，设置角色初始位置 ->","completion":" “when green flag clicked\",\"go to x: [-10] y: [20]\",\"set size to [90] %\",\"switch costume to [lb stance]\",\"show\"\n"}
{"prompt":"点击绿旗，角色变成阴影效果 ->","completion":" “when green flag clicked\",“set [brightness] effect to [-100]\",\"forever\",\"next costume\",\"wait [0.3] seconds\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [left arrow] key pressed\",\"switch costume to [jo pop left]\"\n"}
{"prompt":"点击箭头按钮，改变角色动作 ->","completion":" “when [down arrow] key pressed\",\"switch costume to [jo pop down]\"\n"}
{"prompt":"点击空格键，使角色跳跃 ->","completion":" “when [space] key pressed\",\"repeat [10]\",\"change y by [10]\",“repeat [10]\",\"change y by [-10]\"\n"}
{"prompt":"点击绿旗，移动障碍物 ->","completion":" “when green flag clicked\",“forever”，\"go to x: [240] y: [-145]\"，“glide [3] secs to x: [-240] y: [-145]\"\n"}
{"prompt":"点击绿旗，使角色说话 ->","completion":" “when green flag clicked\",\"go to x: [-50] y: [60]\",\"say [My name is Kiki!] for [2] seconds\"\n"}
{"prompt":"点击角色，播放音效，使角色动起来 ->","completion":" “when [space] key pressed\",“start sound [Chirp]\",\"repeat [4]\",“switch costume to [monkey-a]\",\"wait [0.2] seconds\",“switch costume to [monkey-b]\",\"wait [0.2] seconds\"\n"}
{"prompt":"点击角色，改变状态 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [drink]\",\"wait [1] seconds\",\"switch costume to [glass water-b]\",start sound [Water Drop]\",\"wait [1] seconds\",\"switch costume to [glass water-a]\"\n"}
{"prompt":"角色收到信息，进行喂水，回到原位 ->","completion":" \"when i receive [drink]\",“glide [1] secs to [Glass water]\",\"wait [1] seconds\",“glide [1] secs to x: [-50] y: [60]\"\n"}
{"prompt":"点击小球，播放音乐，并跳动 ->","completion":" “when the sprite clicked\",\"go to [front] layer\",\"broadcast [play]\",\"wait until touching [Monkey] ?\",\"start sound [Boing]\",\"repeat [10]\",\"change by [-5]\",\"repeat [10]\",\"change by [5]\"\n"}
{"prompt":"点击绿旗，让角色到舞台顶端 ->","completion":" “when green flag clicked\",“go to [random position]\",\"set y to [180]\"\n"}
"""
PROMPT_NEW = json.load(open("./scratch_prompt.json", "r"))


def chatgpt_extract_code(text):
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""Extract the code contained contained within {text} and output in JSON format, including a key: "code"."""
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    print(agent_reply, type(agent_reply))
    agent_reply = json.loads(agent_reply)["code"]
    if isinstance(agent_reply, list):
        return agent_reply
    elif isinstance(agent_reply, str):
        return agent_reply.splitlines()
    else:
        return f"{agent_reply},Not valid:{type(agent_reply)}, please check the content"


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


def generate_code_step(content, steps):
    '''
    使用哪些模块（Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables）
    运动、外观、声音、事件、控制、侦测、运算、变量
    '''
    code_agent = []
    if steps == "step1":
        code_agent.append({
            "role":
            "user",
            "content":
            f"""
            Solve a question answering task with interleaving Thought. Please select the answer from the Scratch 3.0 categories below: Motion,Looks,Sound,Events,Control,Sensing,Operators,Variables.
            Here are some examples.
            Question:How do I make a character walk from sitting to right?
            Answer:Use Motion to control character movement, Looks to switch character actions, and Control to repeat execution.
            Question:How do I use the keyboard to control my character's movement?
            Answer:Use Motion to control character movement and Events to detect keyboard input.
            Question:{content}
            """
        })
    elif steps == "step2":
        code_agent.append({
            "role":
            "user",
            "content":
            f"""
            Solve a question answering task with interleaving Thought. Please provide your answer based on the Scratch Wiki Blocks.
            Here are some examples.
            {PROMPT_NEW}
            Question:{content}
            """
        })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    return agent_reply


def chatgpt_extract_step1(text):
    code_agent = []
    code_agent.append({
        "role":
        "user",
        "content":
        f"""Module categories: Looks, Sound, Events, Control, Sensing, Operators, Variables. Your task is to extract the module categories contained within <{text}>, and output them in JSON format, including a key: "type"."""
    })
    agent_reply = create_chat_completion(model=MODEL,
                                         messages=code_agent,
                                         temperature=0)
    print(agent_reply)
    agent_reply = json.loads(agent_reply)["type"]
    if isinstance(agent_reply, list):
        return ["scratchCategoryId-"+reply.lower() for reply in agent_reply]
    elif isinstance(agent_reply, str):
        return ["scratchCategoryId-"+agent_reply.lower()]
    else:
        print(f"Not valid:{type(agent_reply)}, please check the content")


def chatgpt_extract_step2(step2):
    motion_blocks = MotionBlocks()
    looks_blocks = LooksBlocks()
    sound_blocks = SoundBlocks()
    events_blocks = EventsBlocks()
    control_blocks = ControlBlocks()
    sensing_blocks = SensingBlocks()
    ass_block = AssembleBlocks(motion_blocks, looks_blocks, sound_blocks,
                               events_blocks, control_blocks, sensing_blocks)
    extracted_reply = chatgpt_extract_code(step2)
    block_list = cal_similarity(extracted_reply, ass_block)
    block_list = [block for block in block_list if block]
    return block_list


if __name__ == "__main__":
    pass
