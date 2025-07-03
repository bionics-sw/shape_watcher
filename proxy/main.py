from fastapi import FastAPI, Form, Request, status, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.responses import JSONResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class VitalInfo:
    person_identifier: int = 1
    hr: int = 0
    sbp: str = ""
    dbp: str = ""
    spo2: str = ""
    lfhf: str = ""
    ppg: str = "DEADBEAFDEADBEAF"
    measured_at: str = ""
    ppg_reliability: int = 0
    spo2_reliability: int = 0
    spo2_sd: str = "0"

vitalinfo = VitalInfo()
'''
ppgchart = json.loads("{type: 'line', data: {"\
      "datasets: [{ label: 'IR',"\
          "data: [],"\
          "borderColor: 'rgba(255,0,0,1)', backgroundColor: 'rgba(0,0,0,0)' },"\
        "{ label: 'RED',"\
          "data: [],"\
          "borderColor: 'rgba(0,0,255,1)', backgroundColor: 'rgba(0,0,0,0)' } ], },}")
'''

irstring = ""
redstring = ""

def le_string_to_int(hex_string):
    # Convert to bytes in little-endian order
    byte_data = bytes.fromhex(hex_string)
    # Convert from little-endian bytes to integer
    return int.from_bytes(byte_data, byteorder='little')

def str_to_intlist(bytestrings: str):
    global irstring, redstring
    irstring = ""
    redstring = ""
    for i in range(1032):
        irstr = bytestrings[i*8:i*8+8]
        irstring = irstring + str(le_string_to_int(irstr)) + ", "
    for i in range(1033,2064):
        redstr = bytestrings[i*8:i*8+8]
        redstring = redstring + str(le_string_to_int(redstr)) + ", "

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html",
        {"request": request,
         "message": "Cobra FastAPI",
         "identifier": "0",
         "vitalinfo": vitalinfo,
         "irstring": irstring,
         "redstring": redstring})

@app.get("/api/v1/people/{people_id}")
async def get_people(people_id: int):
    return {
        "id": people_id,
        "mini_pc_id": 1,
        "person_identifier": 1,
        "uuid": "0314762d-5ce7-470b-b2b1-63c32bf2e70f",
        "created_at": "2024-04-17T14:19:07.210+09:00",
        "updated_at": "2024-05-13T11:48:25.475+09:00",
        "email": "taro@abc.com",
        "name": "山田 太郎",
        "send_email": "true",
        "token": "DIR29Fsni1DNOgWHkj85CA"
    }

# In-memory users list for demonstration
users_db = [
    {
        "person_identifier": 1,
        "email": "taro@abc.com",
        "name": "山田 太郎",
        "send_email": "true"
    },
    {
        "person_identifier": 2,
        "email": "hanako@abc.com",
        "name": "花子 山田",
        "send_email": "false"
    }
]

@app.get("/api/v1/people")
async def get_all_people():
    return JSONResponse(content=users_db, status_code=200)

@app.post("/api/v1/vital_signs")
async def post_vital(\
    person_identifier: int = Form(), hr: int = Form(),\
    sbp: str = Form(), dbp: str = Form(), spo2: str = Form(),\
    lfhf: str = Form(), ppg: str = Form(), measured_at: str = Form(),\
    ppg_reliability: int = Form(), spo2_reliability: int = Form(), spo2_sd: str = Form()):
    global vitalinfo
    vitalinfo.person_identifier = person_identifier
    vitalinfo.hr = hr
    vitalinfo.sbp = sbp
    vitalinfo.dbp = dbp
    vitalinfo.spo2 = spo2
    vitalinfo.lfhf = lfhf
    vitalinfo.ppg = ppg
    vitalinfo.measured_at = measured_at
    vitalinfo.ppg_reliability = ppg_reliability
    vitalinfo.spo2_reliability = spo2_reliability
    vitalinfo.spo2_sd = spo2_sd
    str_to_intlist(vitalinfo.ppg)
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)

@app.post("/api/v1/people")
async def create_people(
    person_identifier: int = Body(...),
    email: str = Body(...),
    name: str = Body(...),
    send_email: str = Body(...)
):
    # Dummy response, echoing back the received data
    return JSONResponse(content={
        "person_identifier": person_identifier,
        "email": email,
        "name": name,
        "send_email": send_email
    }, status_code=200)

@app.delete("/api/v1/people/{person_identifier}")
async def delete_people(person_identifier: int):
    global users_db
    # Remove user with matching person_identifier
    users_db = [user for user in users_db if user["person_identifier"] != person_identifier]
    return JSONResponse(content={"result": "deleted", "person_identifier": person_identifier}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

