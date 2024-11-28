import openai
import dotenv
dotenv.load_dotenv()
import os
import time
from typing import List
import json

with open(os.path.join(os.getcwd(), "model_prompts.json") ,"r", encoding="latin-1") as f:
    prompts_file = json.load(f)

from openai import OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

set_str = ""

def query_GPT(prompts : List):

    if not os.path.exists(os.path.join(os.getcwd(), "documentation", "models", set_str)):
        os.makedirs(os.path.join(os.getcwd(), "documentation", "models", set_str))
        print("Directory Created")
    else:
        print("Directory Exists")

    for prompt in prompts:

        gen_file_name = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a file name generator. Generate a short file name with underscores,"
                            "no file extension format and that suits the user query prompt"},
                {"role": "user",
                 "content": prompt}
            ],
        )
        file_name = gen_file_name.choices[0].message.content
        print(f"File Name is {file_name}")

        question = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a summarizing assistant. Summarize longer queries into shorter meaningful query"
                            "and Export your response in markdown formatting"},
                {"role": "user",
                 "content": prompt}
            ],
        )

        answer = client.chat.completions.create(
            model="gpt-4", # Use gpt-4o
            messages=[
                {"role": "system",
                 "content": "You are a helpful scientific assistant. Export response in markdown formatting"},
                {"role": "user",
                 "content": prompt}
            ],
        )

        with open(os.path.join(os.getcwd(), "documentation", "models", set_str,
                               f"{file_name}_{str(int(time.time()))}.md"), 'w') as f:
            f.write(question.choices[0].message.content)
            f.write(answer.choices[0].message.content)

# print(completion.choices[0].message.content)

def iterate_nested_dict(data):
    values = []
    for key, value in data.items():
        if isinstance(value, str):
            values.append(value)
        elif isinstance(value, dict):
            values.extend(iterate_nested_dict(value))
    return values

if __name__ == "__main__":

    # set_str = "framenet_frames_cutting"
    # print(type(prompts_file[set_str]), len(prompts_file[set_str]))
    # query_GPT(prompts_file[set_str])

    set_str = "emotional_and_affective_models"
    gpt_model_prompts = iterate_nested_dict(prompts_file[set_str])
    query_GPT(gpt_model_prompts)

    print("Completed")