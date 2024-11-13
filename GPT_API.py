import openai
import dotenv
dotenv.load_dotenv()
import os
import time
from typing import List
import json

with open(os.path.join(os.getcwd(), "all_prompts.json") ,"r", encoding="latin-1") as f:
    prompts = json.load(f)

from openai import OpenAI
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

set_str = ""

def query_GPT(prompts : List):

    if not os.path.exists(os.path.join(os.getcwd(), "documentation", "External", "GPTresponses", set_str)):
        os.makedirs(os.path.join(os.getcwd(), "documentation", "External", "GPTresponses", set_str))
        print("Directory Created")
    else:
        print("Directory Exists")

    for prompt in prompts:

        gen_file_name = client.chat.completions.create(
            model="gpt-4o-mini",
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
            model="gpt-4o", # Use gpt-4o
            messages=[
                {"role": "system",
                 "content": "You are a helpful scientific assistant. Export response in markdown formatting"},
                {"role": "user",
                 "content": prompt}
            ],
        )

        with open(os.path.join(os.getcwd(), "documentation", "External", "GPTresponses", set_str,
                               f"{file_name}_{str(int(time.time()))}.md"), 'w') as f:
            f.write(question.choices[0].message.content)
            f.write(answer.choices[0].message.content)

# print(completion.choices[0].message.content)

if __name__ == "__main__":

    set_str = "framenet_frames_cutting"

    print(type(prompts[set_str]), len(prompts[set_str]))

    query_GPT(prompts[set_str])

    print("Completed")