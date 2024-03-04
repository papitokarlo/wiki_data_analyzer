from bson import ObjectId
from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.templating import Jinja2Templates
import wikipediaapi

from wiki_generator.app.models import WikiData
from wiki_generator.utils.common import load_request
from wiki_generator.defaults.connection import openai_connection
from wiki_generator.utils.db_connection import db


templates = Jinja2Templates(directory="./static")
limiter = Limiter(key_func=get_remote_address)

async def healthcheck(request: Request):
    return JSONResponse({"status": "ok"})

@load_request
@limiter.limit("5/minute")
async def search(request: Request):
    title = request.data.get('title', None)
    user_agent = "Croco_TO_Wiki/1.0 (begadze.zura@gmail.com)"
    wiki_wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language='en')
    page = wiki_wiki.page(title)

    if page.exists():
        result = {"topic": title, "data": page.text}
    else:
        result = {"topic": title, "data": f"Error: Wikipedia page for '{title}' does not exist."}

    return JSONResponse(result, status_code=200)

@load_request
@limiter.limit("5/minute")
async def data_analysis(request: Request):
    input_text = request.data.get('data', None)
    if not input_text:
        raise HTTPException(detail="Input text is required", status_code=400)
    
    prompt = f"Summarize the following text :\n{input_text}"
    stream = openai_connection.chat.completions.create(
        model= "gpt-3.5-turbo",
        messages= [{
            "role": "user",
            "content": f"{prompt}"
        }],
        temperature= 0.7
    )
    content = stream.choices[0].message.content 
    Wiki_Data_Collection = db.get_collection("WikiData")
    doc = await Wiki_Data_Collection.find_one({"input": input_text})
    if not doc:
        obj = WikiData(input=request.data.get('data'), output=content)  
        Wiki_Data_Collection.insert_one(obj.dict()) 
    else:
        doc['search_count'] += 1
        Wiki_Data_Collection.update_one({
            "_id": doc['_id']
        }, 
        {
            "$set": {"search_count": doc['search_count']}
        })

    return JSONResponse({'content': content}, status_code=200)

@load_request
async def list_wiki_data(request: Request):
    Wiki_Data_Collection = db.get_collection("WikiData")
    cursor = Wiki_Data_Collection.find()
    response = []
    async for document in cursor:
        document['_id'] = str(document['_id'])
        document['created_at'] = document['created_at'].isoformat()
        document['last_occurrence'] = document['last_occurrence'].isoformat()
        response.append(document)

    return JSONResponse({'data': "response"}, status_code=200)

@load_request
async def retrieve_wiki_data(request: Request):
    data_id = request.path_params['pk']
    Wiki_Data_Collection = db.get_collection("WikiData")
    object_id = ObjectId(data_id)
    document = await Wiki_Data_Collection.find_one({"_id": object_id})
    if document:
        document['_id'] = str(document['_id'])
        document['created_at'] = document['created_at'].isoformat() 
        document['last_occurrence'] = document['last_occurrence'].isoformat()
        return JSONResponse(content={"data": document}, status_code=200)
    else:
        raise HTTPException(detail="Document not found", status_code=404)


async def docs(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})
