import csv
from datetime import datetime
from io import StringIO
from bson import ObjectId
from fastapi import HTTPException
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse, Response
from starlette.templating import Jinja2Templates
import wikipediaapi

from wiki_generator.app.models import WikiData
from wiki_generator.utils.common import load_request
from wiki_generator.defaults.connection import openai_connection


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
        result = {
            "topic": title, 
            "data": f"Error: Wikipedia page for '{title}' does not exist."
        }

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
    wiki_data = await WikiData.find_one({"input": input_text})
    if wiki_data:
        wiki_data.search_count += 1
        wiki_data.last_occurrence = datetime.utcnow()  
        fields_to_update = {
            WikiData.search_count: wiki_data.search_count,
            WikiData.last_occurrence: wiki_data.last_occurrence,
        }
        await wiki_data.set(fields_to_update)
    else:
        wiki_data = WikiData(input=input_text, output=content, search_count=1)
        await wiki_data.insert()

    return JSONResponse({'content': content}, status_code=200)

@load_request
async def list_wiki_data(request: Request):
    wiki_data_list = await WikiData.find_all().to_list()
    response = [{
        "input": data.input, 
        "output": data.output, 
        "_id": str(data.id), 
        "created_at": data.created_at.isoformat(), 
        "last_occurrence": data.last_occurrence.isoformat()
        } for data in wiki_data_list]

    return JSONResponse({'data': response}, status_code=200)

@load_request
async def retrieve_wiki_data(request: Request):
    data_id = request.path_params['pk']
    wiki_data = await WikiData.get(ObjectId(data_id))
    if wiki_data:
        response = {
            "input": wiki_data.input,
            "output": wiki_data.output,
            "_id": str(wiki_data.id),
            "created_at": wiki_data.created_at.isoformat(),
            "last_occurrence": wiki_data.last_occurrence.isoformat()
        }
        return JSONResponse(content={"data": response}, status_code=200)
    else:
        raise HTTPException(detail="Document not found", status_code=404)

@load_request
async def export_csv(request: Request):
    wiki_data_list = await WikiData.find_all().to_list()
    data = []
    fields = ["id", "input", "output", "created_at", "last_occurrence", "search_count", "is_deleted"]
    for document in wiki_data_list:
        document_dict = document.dict()        
        document_dict['id'] = str(document_dict['id'])
        document_dict['created_at'] = document_dict['created_at'].isoformat()
        document_dict['last_occurrence'] = document_dict['last_occurrence'].isoformat()
        data.append(document_dict)

    csv_data = StringIO()
    csv_writer = csv.DictWriter(csv_data, fieldnames=fields)
    csv_writer.writeheader()
    csv_writer.writerows(data)

    response = JSONResponse(content={"data": "response"}, status_code=200)
    response.headers["Content-Disposition"] = "attachment; filename=wikidata_export.csv"
    response.headers["Content-Type"] = "text/csv"
    response.content = csv_data.getvalue()

    with open("wikidata_export.csv", "w", newline="", encoding="utf-8") as csv_file:
        csv_file.write(csv_data.getvalue())

    return FileResponse("wikidata_export.csv", filename="wikidata_export.csv", media_type="text/csv")

async def docs(request: Request) -> Response:
    return templates.TemplateResponse("index.html", {"request": request})
