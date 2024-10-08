import base64
from flask import Flask, jsonify, request
from speech import openai_speech
import os
import json
from flask_cors import CORS
from tools import *
from story_dict import StoryInfo
from PIL import Image
import shutil
from code_generation import *
from image_generation import *

app = Flask(__name__)
CORS(app)

os.makedirs("./static", exist_ok=True)
os.makedirs("./static/codes", exist_ok=True)


story_info = StoryInfo()


@app.route("/hello")
def hello():
    return "hello"


@app.route('/test_set', methods=['GET', 'POST'])
def test_set():
    act = request.form.get('act')
    type = request.form.get('type')
    content = request.form.get('content')
    story_info.add(act, type, content)
    return [act, story_info.get_act(act_name=act)]


@app.route('/test_query', methods=['GET', 'POST'])
def test_query():
    id = request.form.get("id")
    ask_term = request.form.get('ask_term')
    return story_info.get_prompt(id, ask_term)


@app.route('/get_audio', methods=['GET', 'POST'])
def get_audio():
    """ transform audio to text and add story info"""
    blob = request.files['file']
    act = request.form.get('act')
    imgid = request.form.get('imgid')
    assert act == "1" or act == "2" or act == "3" or act == "4"
    type = request.form.get('type')
    assert type == "role" or type == "background" or type == "event" or type == "code"
    blob.save(f'static/{act}+{type}+{imgid}.webm')
    try:
        with open(f'static/{act}+{type}+{imgid}.webm', 'rb') as f:
            transcript = client.audio.transcriptions.create(
                language='en',
                model="whisper-1",
                file=f
            )
            print("transcript", transcript)
        content = transcript.text
        print(content)
    except FileNotFoundError as e:
        print("File not found error:", e)
    except IOError as e:
        print("IO error:", e)
    except Exception as e:  # 其他所有异常
        print("get_audio error:", e)
    story_info.add(act, type, imgid, content)
    return jsonify({'status': 'success', 'content': content})


@app.route('/get_description', methods=['GET', 'POST'])
def get_description():
    act = request.form.get('act')
    imgid = int(request.form.get('imgid'))
    assert act == "1" or act == "2" or act == "3" or act == "4"
    type = request.form.get('type')
    assert type == "role" or type == "background" or type == "event" or type == "code"
    print(act, type, imgid)
    if imgid < len(story_info.acts[act][type]):
        Text = story_info.acts[act][type][imgid]
    else:
        # Text = '请输入描述'
        Text = 'text your description'
    print("get_description", Text)

    return jsonify({'Text': Text})


@app.route('/send_description', methods=['GET', 'POST'])
def send_description():
    act = request.form.get('act')
    imgid = int(request.form.get('imgid'))
    assert act == "1" or act == "2" or act == "3" or act == "4"
    type = request.form.get('type')
    assert type == "role" or type == "background" or type == "event" or type == "code"
    print(act, type, imgid)
    Text = request.form.get('Text')
    print(Text)
    try:
        story_info.add(act, type, imgid, Text)
        return jsonify({'Status': ['Success']})
    except:
        return jsonify({'Status': ['Fail']})


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    """return images and sounds"""
    id = request.form.get('id')  # part id
    index_id = request.form.get('index_id')  # current part, which image
    index_id = int(index_id)
    assert id == "1" or id == "2" or id == "3"
    assests_path = f"static/{id}"
    os.makedirs(assests_path, exist_ok=True)
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    output = {'sound': [], 'image': []}
    temp_memory = []
    # query
    content = story_info.get_act(act_name=id, key=askterm)
    print("content", content)
    print("index_id", index_id)
    # user already input
    if len(content) >= index_id+1:
        current_drawing = content[index_id]
        current_drawing_e = translate_to_english(current_drawing)
        print("current_drawing", current_drawing_e)
        for index in range(4):
            output["sound"].append(openai_speech(
                (current_drawing), f"{assests_path}/sound-{index}"))
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=current_drawing_e,
                              save_path=f'{assests_path}/image-{index}'))
    # user not input
    elif len(content) < index_id+1:
        prompt = story_info.get_prompt(id, askterm)
        print("story_info.get_prompt:\n", prompt)
        temp_memory.append(prompt)
        agent_reply = create_chat_completion(model=MODEL,
                                             messages=temp_memory,
                                             temperature=0.7)
        print("agent: ", agent_reply)
        if '\n' not in agent_reply:
            raise f"ERROR! Please check {agent_reply}"
        reply_splited = split_to_parts(agent_reply)
        if len(reply_splited) != 4:
            print("the reply is not 4")
            return
        for index, reply in enumerate(reply_splited):
            # print('reply: ',reply)
            reply = translate_to_english(reply)
            output["sound"].append(openai_speech(
                reply, f"{assests_path}/sound-{index}"))
            
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=reply,
                              save_path=f'{assests_path}/image-{index}'))
    else:
        content = content[0]
        # content=translate_to_english(content)

        for index in range(4):
            output["sound"].append(openai_speech(
                translate_to_english(content), f"{assests_path}/sound-{index}"))
            output["image"].append(
                generate_draw(drawing_type=askterm,
                              drawing_content=content,
                              save_path=f'{assests_path}/image-{index}'))
    return jsonify(output)


@app.route('/generate_img_to_img', methods=['GET', 'POST'])
def generate_img_to_img():
    id = request.form.get("id")
    index_id = request.form.get("index_id")
    assests_path = f"static/{id}"
    assert id == "1" or id == "2" or id == "3"
    askterm = request.form.get('askterm')
    assert askterm == "role" or askterm == "background" or askterm == "event"
    os.makedirs(assests_path, exist_ok=True)
    if request.form.get("url") == 'placeholder':
        shutil.copy('static/blank.png', 'static/temp.png')
    else:
        base_img = request.form.get("url").split(',')[1]  # base64
        base_img_bytes = base64.b64decode(base_img)
        img = Image.open(io.BytesIO(base_img_bytes)).convert('RGBA')
        bg = Image.new('RGBA', img.size, (255, 255, 255))
        # TODO 角色背景分开
        # 在背景上粘贴原图像（使用原图像作为遮罩以保留其透明度）
        combined = Image.alpha_composite(bg, img)
        combined.convert('RGB').save('static/temp.png', 'PNG')
    content = story_info.get_act(act_name=id, key=askterm)
    current_role = translate_to_english(content[int(index_id)])
    print("current_role", current_role)
    if askterm == "role":
        content = rule_refine_drawing_prompt_for_role(current_role)
    else:
        content = rule_refine_drawing_prompt(current_role)
    if content != []:
        # image_base64 = generate_image_to_image_v2(
        image_base64 = generate_controlnet(
            prompt=content, base_image="static/temp.png")
        if askterm == "role":
            # rmbg_image = rm_img_bg(image_base64)
            rmbg_image = rm_img_bg_local(
                "image_to_image.png", "rmbg_image.png")
            return jsonify({'status': 'success', 'url': rmbg_image})
        else:
            return jsonify({'status': 'success', 'url': image_base64})
    else:
        return jsonify({'status': 'failed', 'url': None})


@app.route('/save_drawings', methods=['GET', 'POST'])
def save_drawings():
    role_list = json.loads(request.form['role'])
    # print(role_list)
    project_path = "/media/sda1/cyn-workspace/scratch-gui/src/lib/default-project"
    assests_path = f"/media/sda1/cyn-workspace/Scratch-project/ScratchGPT/static/role"
    if os.path.exists(assests_path):
        shutil.rmtree(assests_path)
    os.makedirs(assests_path, exist_ok=True)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
    os.makedirs(project_path, exist_ok=True)
    for i, img in enumerate(role_list):
        img = img.split(',')[1]
        png_path = os.path.join(assests_path, f'{i}.png')
        with open(png_path, "wb") as f:
            f.write(b64decode(img))
        toSVG(png_path, project_path, assests_path)
        if os.path.exists(png_path):
            os.remove(png_path)  # 删除原始PNG图片

    # 处理scene_list
    scene_list = json.loads(request.form['scene'])
    assests_path = f"/media/sda1/cyn-workspace/Scratch-project/ScratchGPT/static/scene/"
    if os.path.exists(assests_path):
        shutil.rmtree(assests_path)
    os.makedirs(assests_path, exist_ok=True)
    for i, img in enumerate(scene_list):
        img = img.split(',')[1]
        png_path = os.path.join(assests_path, f'{i}.png')
        with open(png_path, "wb") as f:
            f.write(b64decode(img))
        toSVG(png_path, project_path, assests_path)
        os.remove(png_path)  # 删除原始PNG图片
    generate_js()
    generate_js_project()
    return jsonify({'status': 'success'})


@app.route('/generate_code', methods=['GET', 'POST'])
def generate_code():
    """
    return code_list
    """
    try:
        os.makedirs('static/codes', exist_ok=True)
        id = request.form.get("id")
        audio_blob = request.files['file']
        # print(id, audio_blob)
        audio_blob.save(f'static/codes/code-question-{id}.webm')
        with open(f'static/codes/code-question-{id}.webm', 'rb') as f:
            transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
            content = transcript.text
            print(content)
        # test
        # content = 'use keyboard to control the movement of up, down, left and right'
        # content = 'let my character say hello, and then move to the edge of the screen and final say goodbye'
        step1 = generate_code_step(content, "step1")
        step2 = generate_code_step(content, "step2")
        # step1, step2 = extract_step(content)
        # print("step1", step1)
        # print("step2", step2)
        audio_base64 = openai_speech(step1, f"static/codes/agent-reply-{id}.mp3")
        # audio_base64 = openai_speech(translate_to_chinese(
        #     step1), f"static/codes/agent-reply-{id}.mp3")
        extracted_step1 = chatgpt_extract_step1(step1)
        # print("extracted_step1", extracted_step1)
        with open(f"static/codes/agent_reply-{id}.json", "w", encoding='utf-8') as f:
            json.dump(extracted_step1, f)
        block_list = chatgpt_extract_step2(step2)
        print("test:", block_list)

        output_json = 'static/codes/block_suggestion.json'
        data = {}
        if os.path.exists(output_json):
            with open(output_json, 'r') as f:
                data = json.load(f)
        data[str(int(id)-1)] = block_list
        with open(output_json, 'w') as f:
            json.dump(data, f, indent=4)
        return jsonify({'file': audio_base64})
    except Exception as e:
        print(str(e))
        # audio = openai_speech(
        #     '输入错误，请点击打勾按钮后重新提问', f"static/codes/agent-error.mp3")
        audio = openai_speech(
            '输入错误，请点击打勾按钮后重新提问', f"static/codes/agent-error.mp3")
        return jsonify({'status': 'fail', 'file': audio})
        # return jsonify({'error': 'An error occurred while processing your request.'})


if __name__ == '__main__':
    # openai_speech("第一幕", f"第一幕.mp3")
    # openai_speech("第二幕", f"第二幕.mp3")
    # openai_speech("第三幕", f"第三幕.mp3")
    # audio_base64 = openai_speech(
    #     '输入错误，请点击打勾按钮后重新提问', f"static/codes/agent-error.mp3")
    app.run(host='0.0.0.0', port=5500, debug=False)
    # extracted_reply = ['event_whenflagclicked', 'switchcostumeto', 'control_wait', 'switchcostumeto', 'control_wait', 'switchcostumeto', 'control_wait', 'switchcostumeto', 'control_wait']
    # block_list = cal_similarity(extracted_reply, ass_block)
    # block_list = [block for block in block_list if block]
    # print(block_list)
