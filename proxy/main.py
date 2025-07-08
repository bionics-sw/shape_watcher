from fastapi import FastAPI, Form, Request, status, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import os
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
#import psycopg2
import datetime

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

irstring = ""
redstring = ""

# Load .env file
#load_dotenv()

# Get the connection string from the environment variable
#connection_string = os.getenv('DATABASE_URL')
# Create a connection pool
connection_pool = ThreadedConnectionPool(
    1,  # Minimum number of connections in the pool
    10,  # Maximum number of connections in the pool
    #connection_string
    host="ep-yellow-grass-aa3kbeuw-pooler.westus3.azure.neon.tech",
    database="neondb",
    user="neondb_owner",
    password="npg_apYyE5TbPlr0"
)

# Check if the pool was created successfully
if connection_pool:
    print("Connection pool created successfully")

# Get a connection from the pool
conn = connection_pool.getconn()
'''
conn = psycopg2.connect(
    host="ep-yellow-grass-aa3kbeuw-pooler.westus3.azure.neon.tech",
    database="neondb",
    user="neondb_owner",
    password="npg_apYyE5TbPlr0"
)
'''
# Create a cursor object
cur = conn.cursor()
# Set the schema
cur.execute('SET search_path TO "cobrahealthcare";')

# Print out all tables in the selected schema for testing
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'cobrahealthcare';")
tables = cur.fetchall()
print('Tables in schema cobrahealthcare:')
for table in tables:
    print(table[0])

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
    print(name)
    conn = connection_pool.getconn()
    if conn is None:
        return JSONResponse(content={"error": "Failed to get a connection from the pool"}, status_code=500)
    # Store received data into the SQL database
    try:
        # Generate RFC3339 datetime with timezone
        now_rfc3339 = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with conn:
            with conn.cursor() as cur:
                cur.execute('SET search_path TO "cobrahealthcare";')
                cur.execute(
                    """
                    INSERT INTO people (
                        person_identifier, email, name, send_email,
                        mini_pc_id, uuid, created_at, updated_at, token
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        person_identifier,
                        email,
                        name,
                        send_email,
                        1,  # mini_pc_id dummy
                        '00000000-0000-0000-0000-000000000000',  # uuid dummy
                        now_rfc3339,  # created_at
                        now_rfc3339,  # updated_at
                        'DUMMYTOKEN123'  # token dummy
                    )
                )
        connection_pool.putconn(conn)
        return JSONResponse(content={
            "person_identifier": person_identifier,
            "email": email,
            "name": name,
            "send_email": send_email,
            "mini_pc_id": 1,
            "uuid": '00000000-0000-0000-0000-000000000000',
            "created_at": now_rfc3339,
            "updated_at": now_rfc3339,
            "token": 'DUMMYTOKEN123',
            "result": "stored in db"
        }, status_code=200)
    except Exception as e:
        connection_pool.putconn(conn)
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.delete("/api/v1/people/{person_identifier}")
async def delete_people(person_identifier: int):
    global users_db
    # Remove user with matching person_identifier
    users_db = [user for user in users_db if user["person_identifier"] != person_identifier]
    return JSONResponse(content={"result": "deleted", "person_identifier": person_identifier}, status_code=200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

