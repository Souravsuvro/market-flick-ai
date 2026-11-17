from datetime import datetime
import hashlib
from dotenv import load_dotenv
load_dotenv()
import json
import uuid
from constants import BASE_URL, KNOWLEDGE_BASE_PATH, RESPONSE_PATH, important_keys, FIGURE_PATH
from core.presentation_generation.agent import create_presentation
from core.investor_analysis.agent import get_investor_analysis
from core.util_agents.chat_agent import chat_with_agent
from core.util_agents.chat_write_agent import chat_write_agent
from core.util_agents.title_generator import generate_title
from core.rag.rag import upload_and_fetch_context
from utils.general_utils import load_response_from_db, get_all_saved_responses
from database.db import get_database
from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, Query, Body, Request
from fastapi.responses import StreamingResponse, FileResponse
import asyncio
from typing import AsyncGenerator
from fastapi.middleware.cors import CORSMiddleware
from custom_types.market_analysis import BusinessAnalysisInput
from custom_types.basetypes import ChatRequest, ChatType, PresentationInput
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from pprint import pformat

from core.market_size_analysis.test_langgraph import build_business_analysis_graph
import os
import gridfs


from core.market_size_analysis.utils import extract_knowledge_base, get_serializable_response, save_response_to_db


os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)
os.makedirs(FIGURE_PATH, exist_ok=True)
os.makedirs(RESPONSE_PATH, exist_ok=True)

os.makedirs('./rag_base', exist_ok=True)
os.makedirs('./rag_base/chunks', exist_ok=True)
os.makedirs('./rag_base/files', exist_ok=True)
os.makedirs('./rag_base/retrieved_context', exist_ok=True)
os.makedirs('./rag_base/sources', exist_ok=True)

# # Load .env file

# # Access environment variables
# mongodb_uri = os.getenv("MONGODB_URI")
# openai_api_key = os.getenv("OPENAI_API_KEY")
# pplx_api_key = os.getenv("PPLX_API_KEY")
# tavily_api_key = os.getenv("TAVILY_API_KEY")
# nvidia_api_key = os.getenv("NVIDIA_API_KEY")

# # Print (for debugging purposes)
# print("tavily_api_key:", tavily_api_key)
# print("OPENAI_API_KEY:", openai_api_key)

set_llm_cache(InMemoryCache())


app = FastAPI()

# Import auth modules
from core.auth.middleware import verify_jwt_token
from core.auth.routes import router as auth_router

origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
if not origins:
    raise RuntimeError("CORS_ORIGINS must contain at least one explicit frontend origin.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Add JWT verification middleware
@app.middleware("http")
async def jwt_middleware(request, call_next):
    return await verify_jwt_token(request, call_next)

# Include auth router
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Python server is running..."}


@app.post("/business-analysis")
async def business_analysis_stream(
    request: Request,
    sector: str = Form(...),
    idea: str = Form(...),
    location: str = Form(...),
    links: list[str] | None = Form(None),
    files: list[UploadFile] | None = Form(None)
) -> StreamingResponse:
    # Derive identity from the verified access token, never from client form data.
    userId = request.state.user_id
        

    print('~'*100)
    print(links, type(links))
    print('~'*100)
    business_input = BusinessAnalysisInput.as_form(
        sector=sector,
        idea=idea,
        location=location,
        files=files,
        links=links
    )
    
    knowledge_base_id = str(uuid.uuid4())
    
    points = []
    if files:
        sources_object = {
            "knowledge_base_id": knowledge_base_id,
            "files": [],
            "links": []
        }
        db = get_database()
        fs = gridfs.GridFS(db)
        # Save files to MongoDB GridFS
        for file in files:
            content = await file.read()
            file_uuid = hashlib.sha256(content).hexdigest()
            gridfs_id = fs.put(content, filename=file.filename)
            file_object = {
                "file_id": file_uuid,
                "file_name": file.filename,
                "gridfs_id": gridfs_id,
                "knowledge_base_id": knowledge_base_id,
                "uploaded_at": datetime.utcnow()
            }
            db["files"].insert_one(file_object)
            sources_object["files"].append({
                "file_id": file_uuid,
                "file_name": file.filename,
                "gridfs_id": str(gridfs_id)
            })

        # Save links to MongoDB
        if links:
            for link in links:
                link_id = hashlib.sha256(link.encode()).hexdigest()
                link_object = {
                    "link_id": link_id,
                    "link_url": link,
                    "knowledge_base_id": knowledge_base_id,
                    "uploaded_at": datetime.utcnow()
                }
                db["links"].insert_one(link_object)
                sources_object["links"].append({
                    "link_id": link_id,
                    "link_url": link
                })

        print(sources_object)
        # No local JSON or file write needed
    
        points = upload_and_fetch_context(knowledge_base_id, f'Idea: {business_input.idea} - Sector: {business_input.sector} - Location: {business_input.location}', sources_object)
     
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            
            yield json.dumps({
                "key": "start",
                "data": "Waaassuupp?",
                "status": "success"
            })


            # basic info from the idea
            title = generate_title(business_input)
            current_date_time = datetime.now().isoformat()
            basic_info = {
                "basic_info_id": knowledge_base_id,
                "basic_info": {
                    "title": title, 
                    "date": current_date_time,
                    "business_idea": business_input.idea,
                    "business_sector": business_input.sector,
                    "business_location": business_input.location
                }
            }

            yield json.dumps({
                "key": "basic_info",
                "data": basic_info,
                "status": "success"
            })

            save_response_to_db(basic_info, knowledge_base_id, user_id=userId, collection_name="basic_info")


            # Create the graph
            graph = build_business_analysis_graph()

            

            # Initial state
            initial_state = {
                "business_analysis_input": business_input,
                "knowledge_base_id": knowledge_base_id,
                "user_id": userId,
                "internal_context_points": points,
                "knowledge_base": "",
                "market_size_data_points": "",
                "market_size_plot_id": "",
                "market_player_table_data": "",
                "market_player_table_id": "",
                "search_queries": "",
                "sources": "",
                "competitors_chart_id": "",
                "competitors_chart_data": "",
                "swot_analysis": "",
                "pestali_analysis": "",
                "roadmap": "",
                "is_last_step": False,
            }

            # Stream the graph execution
            async for event in graph.astream(initial_state):
                try:
                    output_str = ""
                    for node, output in event.items():
                        # Handle knowledge base ID
                        
                        print("streaming", "-"*100)
                        print(output)
                        for key in important_keys:
                            if key in output:
                                try:
                                    yield json.dumps({
                                        "key": key,
                                        "data": get_serializable_response(output[key]),
                                        "status": "success"
                                    })
                                except Exception as e:
                                    yield json.dumps({
                                        "key": key,
                                        "data": output[key],
                                        "status": "error"
                                    })

                    # Optional: add a small delay to prevent overwhelming the client
                    await asyncio.sleep(0.1)

                except Exception as e:
                    yield json.dumps({
                        "key": "error",
                        "data": str(e),
                        "status": "error"
                    })
                    continue

            # Final event to indicate stream completion
            yield json.dumps({
                "key": "data",
                "data": "[DONE]",
                "status": "success"
            })

        except Exception as e:
            yield json.dumps({
                "key": "error",
                "data": str(e),
                "status": "error"
            })

    # Return a StreamingResponse with the async generator
    return StreamingResponse(generate_stream(), media_type="application/json")





@app.post("/previous-analysis/{knowledge_base_id}")
async def previous_analysis_stream(
    request: Request,
    knowledge_base_id: str,
    payload: dict = Body(...)
) -> StreamingResponse:
    user_id = request.state.user_id
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            yield json.dumps({
                "key": "start",
                "data": "Waaassuupp?",
                "status": "success"
            })
            # Create the graph
            
            saved_responses = get_all_saved_responses(knowledge_base_id , user_id)
            # Stream the graph execution
            for key, response in saved_responses.items():
                try:
                    for key in important_keys:
                        if key in response:
                            yield json.dumps({
                                "key": key,
                                "data": response[key],
                                "status": "success"
                            })

                    # Optional: add a small delay to prevent overwhelming the client
                    await asyncio.sleep(0.1)

                except Exception as e:
                    yield json.dumps({
                        "key": "error",
                        "data": str(e),
                        "status": "error"
                    })
                    continue

            # Final event to indicate stream completion
            yield json.dumps({
                "key": "data",
                "data": "[DONE]",
                "status": "success"
            })

        except Exception as e:
            yield json.dumps({
                "key": "error",
                "data": str(e),
                "status": "error"
            })

    # Return a StreamingResponse with the async generator
    return StreamingResponse(generate_stream(), media_type="application/json")


@app.get("/analyses")
async def get_analyses(request: Request):
    user_id = request.state.user_id
    """
    Endpoint to list all file names in the KNOWLEDGEBASE_PATH.

    Returns:
        List[str]: A list of file names in the knowledge base directory.
    """
    
    if user_id is None or user_id.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    try:
        
        db = get_database()
        collection = db['basic_info']
        # Filter analyses based on user_id from the database
        analyses = collection.find({"user_id": user_id}, {"_id": 0})
        
        
        return {
            "analyses": list(analyses),
        }

    except FileNotFoundError:
        return {"error": "File not found"}
    except Exception as e:
        return {"error": str(e)}

    
@app.post("/chat")
async def chat(request: Request, chat_request: ChatRequest):
    knowledge_base_id = chat_request.id
    user_id = request.state.user_id
    
    knowledge_base = extract_knowledge_base(knowledge_base_id)

    if chat_request.type == ChatType.CHAT:
        response = chat_with_agent(input_text=chat_request.message, chat_history=chat_request.chat_history, knowledge_base=knowledge_base, knowledge_base_id=knowledge_base_id, user_id=user_id)
    elif chat_request.type == ChatType.WRITE:
        response = chat_write_agent(id=chat_request.id, input=chat_request.message, chat_history=chat_request.chat_history, component_keys=chat_request.component_keys, knowledge_base=knowledge_base, user_id=user_id)
    return response




@app.post("/generate-presentation")
async def generate_presentation(presentation_input: PresentationInput):
    id = presentation_input.id
    template_name = presentation_input.template_name
    response = create_presentation(id=id, template_name=template_name)

    return {
        "message": "Presentation generated successfully",
        "file_link": f"{BASE_URL}/download-presentation/{id}.pptx"
    }


@app.get("/download-presentation/{id}.pptx")
async def download_file(id: str):
    file_path = f"{RESPONSE_PATH}/presentation_{id}.pptx"
    print(file_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=f"presentation_{id}.pptx",
        media_type="application/octet-stream"
    )
  
@app.post("/investor-analysis/{id}")
async def investor_analysis(id: str):
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            async for s in get_investor_analysis(id):
                message = s["messages"][-1]
                if isinstance(message, tuple):
                    # SSE requires "data: <content>\n\n"
                    yield json.dumps({"data": message})
                else:
                    yield json.dumps({"data": str(message.pretty_repr())})
        
        except Exception as e:
            yield json.dumps({"event": "error", "data": str(e)})

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",  # Allow frontend to access
    }
    
    return StreamingResponse(generate_stream(), media_type="application/json", headers=headers)


@app.get("/investor-profiles/{id}")
async def investor_profiles(id: str):
    repsonse = load_response_from_db(f"investors_and_companies_{id}")
    return repsonse

