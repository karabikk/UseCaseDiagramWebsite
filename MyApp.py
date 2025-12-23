import os
import io
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI  
import requests           
from google import genai



load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret-key")

# Allowed file extensions
ALLOWED = {"csv"}
def allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

# =============== API KEYS (set in .env) ===============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY") 
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# OpenAI client (ChatGPT)
openai_client = OpenAI(api_key=OPENAI_API_KEY)
# Gemini client 
gemini_client = genai.Client(api_key=GEMINI_API_KEY) 
deekseek_client =OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")



def normalize_openai_text(resp):
    # OpenAI Responses API often exposes .output_text
    txt = getattr(resp, "output_text", None)
    if txt:
        return txt
    # fallback: try to dig into the content
    try:
        return resp.output[0].content[0].text
    except Exception:
        return "(No text output returned)"

#function to call the chatGPT API
def my_chatgpt(csv_text,user_prompt): #function to call the chatGPT API

    # chain 1: Rewrite
    rsp1 = openai_client.responses.create(
        model="gpt-5",
        input=[
            {"role": "user","content": f"You are a Software System Engineer using the IEEE 29148 SRS standard. Your task is to rewrite software functional requirements into a professional system requirement {csv_text}"}
            ]
    )
    stage1 = normalize_openai_text(rsp1)
    

    # chain 2: Use Cases
    rsp2 = openai_client.responses.create(
        model="gpt-5",
        input=[{
            "role": "user", "content": f"You are a Software Systems Engineer who is given the following task: please extract actors from the functional requirements and describe their goals. Then convert their goals into use cases. Output only the use cases.{stage1}"}
        ]
    )
    stage2 = normalize_openai_text(rsp2)

    # chain 3: Use cases
    rsp3 = openai_client.responses.create(
        model="gpt-5",
        input=[
            {"role": "user", "content": f"You are a Software Systems Engineer tasked with designing a UML use case diagram; given the following use cases, decide the appropriate relationships between them and then create a use case diagram using PlantUML notation.{stage2}"}
            ]   
    )
    stage3 = normalize_openai_text(rsp3)

    # chain 4: PlantUML
    rsp4 = openai_client.responses.create(
        model="gpt-5",
        input=[{
            "role": "user", "content": f"You are a Software Systems Engineer who is assigned the following: remove any actor-to-use case associations where the use case is already connected through an <<extend>> or <<include>> relationship.{stage3}"}
        ]
    )
    stage4 = normalize_openai_text(rsp4)

    rsp5 = openai_client.responses.create(
        model="gpt-5",
        input=[{
            "role": "user", "content": f"You are given three tasks. Your first task is to convert the actor use case association arrows into plain, non-directional lines. Your second task is to find any <<extend>> relationship and rewrite it using a dotted arrow with UP directional modifier using this format: X .up.¿ Y : <<extend>>. Then, your third task is find any <<include>> relationship and rewrite it using a dotted arrow with DOWN directional modifier using this format: X .down.¿ Y :<<include>>.{stage4}"}
        ]
    )
    stage5 = normalize_openai_text(rsp5)
   
        

    return {
        "provider": "ChatGPT",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3,
        "stage4": stage4,
        "stage5": stage5,
        "suggested_name": "csv-analysis.txt",
    }


#function to call the deepseek API
def my_deepseek(csv_text, user_prompt):
    resp = deekseek_client.chat.completions.create(
           model="deepseek-chat",
           messages = [
                {"role": "user", "content": f""" You are a Software System Engineer using the IEEE 29148 SRS standard. Your task is to rewrite software functional requirements into a professional system requirement :{csv_text}"""}
           ]
    )
    chain1 = resp.choices[0].message.content.strip()

    resp2 = deekseek_client.chat.completions.create(
        model="deepseek-chat",
        messages= [
               {"role": "user", "content": f"You are a Software Systems Engineer who is given the following task: please extract actors from the functional requirements and describe their goals. Then convert their goals into use cases. Output only the use cases.{chain1}"}
        ]
    )
    chain2 = resp2.choices[0].message.content.strip()

    resp3 = deekseek_client.chat.completions.create(
        model="deepseek-chat",
        messages= [
            {"role": "user", "content": f"You are a Software Systems Engineer tasked with designing a UML use case diagram; given the following use cases, decide the appropriate relationships between them and then create a use case diagram using PlantUML notation.{chain2}"}
        ]
    )
    chain3 = resp3.choices[0].message.content.strip()

    resp4 = deekseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": f"You are a Software Systems Engineer who is assigned the following: remove any actor-to-use case associations where the use case is already connected through an <<extend>> or <<include>> relationship.{chain3}"}
        ]
    )
    chain4 = resp4.choices[0].message.content.strip()

    resp5 = deekseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": f"You are given three tasks. Your first task is to convert the actor use case association arrows into plain, non-directional lines. Your second task is to find any <<extend>> relationship and rewrite it using a dotted arrow with UP directional modifier using this format: X .up.¿ Y : <<extend>>. Then, your third task is find any <<include>> relationship and rewrite it using a dotted arrow with DOWN directional modifier using this format: X .down.¿ Y :<<include>>.{chain4}"}
        ]
    )
    chain5 = resp5.choices[0].message.content.strip()

    return {
        "provider": "DeepSeek",
        "stage1": chain1,
        "stage2": chain2,
        "stage3":chain3,
        "stage4": chain4,
        "stage5": chain5,
        "suggested_name": "csv-analysis.txt",
    }

#function to call the gemini API
def my_gemini(csv_txt, user_prompt):

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"You are a Software System Engineer using the IEEE 29148 SRS standard. Your task is to rewrite software functional requirements into a professional system requirement  {csv_txt}"
        )
    chain1 = response.text
   

    response2 = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents = f"You are a Software Systems Engineer who is given the following task: please extract actors from the functional requirements and describe their goals. Then convert their goals into use cases. Output only the use cases.{chain1}"
    )
    chain2 = response2.text

    response3 = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents = f"You are a Software Systems Engineer tasked with designing a UML use case diagram; given the following use cases, decide the appropriate relationships between them and then create a use case diagram using PlantUML notation.{chain2}"
    )
    chain3 = response3.text


    response4 = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents = f"You are a Software Systems Engineer who is assigned the following: remove any actor-to-use case associations where the use case is already connected through an <<extend>> or <<include>> relationship.{chain3}"
    )
    chain4 = response4.text

    response5 = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents = f"You are given three tasks. Your first task is to convert the actor use case association arrows into plain, non-directional lines. Your second task is to find any <<extend>> relationship and rewrite it using a dotted arrow with UP directional modifier using this format: X .up.¿ Y : <<extend>>. Then, your third task is find any <<include>> relationship and rewrite it using a dotted arrow with DOWN directional modifier using this format: X .down.¿ Y :<<include>>.{chain4}"
    )
    chain5 = response5.text
    
    return {
        "provider": "Gemini",
        "stage1": chain1,
        "stage2": chain2,
        "stage3":chain3,
        "stage4": chain4,
        "stage5": chain5,
        "suggested_name": "csv-analysis.txt",
    }

# ------------------ Routes ------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        f = request.files["csvfile"]   # <input type="file" name="csvfile">
        user_prompt= request.form.get("userrequirements", "").strip()   # <textarea name="userrequirements">
        mode = request.form.get("mode", "chatGPT")  # chatGPT / Gemini / DeepSeek / Pro

     
        #CASE 1: USER UPLOADS A CSV FILE
        if f.filename.lower().endswith(".csv"):
            df = pd.read_csv(f) # reads and saves the file into a pandas datagram
            csv_text = df.to_csv(index=False) #converts it to a csv file
        # CASE 2: USER PASTES FUNCTIONAL REQUIREMENTS
        elif user_prompt:
            csv_text = user_prompt
        # CASE 3: USER DOES NEITHER OF THE ABOVE
        else:
            flash("Please upload a CSV file OR paste text.")
            return redirect(request.url)
            
        if mode == "chatGPT":
            result = my_chatgpt(csv_text, user_prompt)
        elif mode == "Gemini":
            result = my_gemini(csv_text, user_prompt)
        elif mode == "DeepSeek":
            result = my_deepseek(csv_text, user_prompt)
        else:
            flash("-----")
            return redirect(request.url)

          

        return render_template(
                "result.html",
                provider=result["provider"],
                stage1=result["stage1"],
                stage2=result["stage2"],
                stage3=result["stage3"],
                stage4=result["stage4"],
                stage5=result["stage5"],
                suggested_name=result["suggested_name"],
            )
    # GET
    return render_template("index.html")



if __name__ == "__main__":
    app.run(debug=True)
