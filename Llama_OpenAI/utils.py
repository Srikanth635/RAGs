import os
import base64
import fitz
from io import BytesIO
from PIL import Image
import requests
from openai import OpenAI
import ollama
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)


def get_b64_image_from_content(image_content):
    img = Image.open(BytesIO(image_content))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def is_graph(image_content):
    res = describe_image(image_content)
    return any(keyword in res.lower() for keyword in ["graph", "plot", "chart", "table"])


def process_graph(image_content):
    deplot_description = process_graph_deplot(image_content)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            # {"role": "system",
            #  "content": "You are a file name generator. Generate a short file name with underscores,"
            #             "no file extension format and that suits the user query prompt"},
            {"role": "user",
             "content": "Your responsibility is to explain charts. "
                        "You are an expert in describing the responses of linearized tables into plain English text for LLMs to use. Explain the following linearized table. " + deplot_description}
        ],
        temperature=0.20,
        top_p=0.20,
        stream=False,
        max_tokens=1024,
    )

    return response.choices[0].message.content


def describe_image(image_content):
    # Encode the image to base64
    image_b64 = get_b64_image_from_content(image_content)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI API Key is not set. Please set the OPENAI_API_KEY environment variable.")
    print("Trying OLLAMA")
    try:
        # Generate a description using the Ollama llama3.2-vision model
        response = ollama.chat(
            model='llama3.2-vision',
            messages=[
                {
                    'role': 'user',
                    'content': 'Describe what you see in this image.',
                    'images': [image_b64]
                }
            ]
        )
        print("describe Response : ", response.keys())
        print("describe Response : ", response['message'])
        return response['message']
    except Exception as e:
        print(f"An error occurred: {e}")

def describe_image_openai(image_content):
    # Encode the image to base64
    image_b64 = get_b64_image_from_content(image_content)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI API Key is not set. Please set the OPENAI_API_KEY environment variable.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What’s in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"new_logs:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    print(response.json())
    return response_json['choices'][0]['message']['content']


def process_graph_deplot(image_content):
    image_b64 = get_b64_image_from_content(image_content)
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI API Key is not set. Please set the OPENAI_API_KEY environment variable.")
    print("DEPLOT")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Generate underlying new_logs table of the figure below"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"new_logs:image/jpeg;base64,{image_b64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    print("PROMPTING DEPLOT")
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    print(response.json())
    return response_json['choices'][0]['message']['content']


def extract_text_around_item(text_blocks, bbox, page_height, threshold_percentage=0.1):
    before_text, after_text = "", ""
    vertical_threshold_distance = page_height * threshold_percentage
    horizontal_threshold_distance = bbox.width * threshold_percentage

    for block in text_blocks:
        block_bbox = fitz.Rect(block[:4])
        vertical_distance = min(abs(block_bbox.y1 - bbox.y0), abs(block_bbox.y0 - bbox.y1))
        horizontal_overlap = max(0, min(block_bbox.x1, bbox.x1) - max(block_bbox.x0, bbox.x0))

        if vertical_distance <= vertical_threshold_distance and horizontal_overlap >= -horizontal_threshold_distance:
            if block_bbox.y1 < bbox.y0 and not before_text:
                before_text = block[4]
            elif block_bbox.y0 > bbox.y1 and not after_text:
                after_text = block[4]
                break

    return before_text, after_text


def process_text_blocks(text_blocks, char_count_threshold=500):
    current_group = []
    grouped_blocks = []
    current_char_count = 0

    for block in text_blocks:
        if block[-1] == 0:  # Check if the block is of text type
            block_text = block[4]
            block_char_count = len(block_text)

            if current_char_count + block_char_count <= char_count_threshold:
                current_group.append(block)
                current_char_count += block_char_count
            else:
                if current_group:
                    grouped_content = "\n".join([b[4] for b in current_group])
                    grouped_blocks.append((current_group[0], grouped_content))
                current_group = [block]
                current_char_count = block_char_count

    # Append the last group
    if current_group:
        grouped_content = "\n".join([b[4] for b in current_group])
        grouped_blocks.append((current_group[0], grouped_content))

    return grouped_blocks


def save_uploaded_file(uploaded_file):
    temp_dir = os.path.join(os.getcwd(), "vectorstore", "ppt_references", "tmp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file_path = os.path.join(temp_dir, uploaded_file.name)

    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(uploaded_file.read())

    return temp_file_path