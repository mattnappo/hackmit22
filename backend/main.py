from fastapi import FastAPI, File, UploadFile, Form
from typing import Optional
from pydantic import BaseModel
import json
from typing import List

import backend.ai as ai
import backend.state as state

class Course(BaseModel):
    user: str
    course: str
    summary: Optional[str]
    calendar: Optional[dict]
    gpa: Optional[dict]

class QA(BaseModel):
    prompt: str
    user: str

app = FastAPI()
state = state.State()

@app.get("/test/user/{user}")
def test_user(user: str):
    with open("test.json") as f:
        return json.loads(f.read())

@app.post("/upload/")
async def upload_syllabus(user: str = Form(), course: str = Form(), syllabus: UploadFile = Form()):
    course = course.lower()
    # Store in DB
    contents = syllabus.file.read()
    status = state.store_syllabus(user, course, syllabus.filename, contents)
    if status['status'] != 'ok':
        return status

    # Read text from pdf
    text = ai.extract_text(status['abspath'])
    # Do ML
    info_obj = await ai.get_class_info(text)

    #print(info_obj)
    #print(text)
    # Store output of ML in db
    status = state.store_ml(user, course, info_obj, text)
    return status

@app.post("/upload_all/fut/") # Future
def upload_syllabi(user: str = Form(), syllabi: List[UploadFile] = Form()):
    for syllabus in syllabi:
        upload_syllabus(user, syllabus)
    return {"status": "ok"}

@app.get("/user/{user}")
def get_user(user: str):
    return state.get_user(user)

@app.get("/full_qa")
def naive_q_and_a(req: QA):
    # concatenate all data together
    knowledge = state.get_user_knowledge(req.user)

    # Make req to davinci
    answer = ai.q_and_a(knowledge, req.prompt)
    return {"answer": answer}

@app.get("/clear")
def clear():
    state.clear()
    
    return {"status": "ok"}

