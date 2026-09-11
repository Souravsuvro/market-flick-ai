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
from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, Query, Body
from fastapi.responses import StreamingResponse, FileResponse
import asyncio
from typing import AsyncGenerator
from fastapi.middleware.cors import CORSMiddleware
from custom_types.market_analysis import BusinessAnalysisInput
from custom_types.basetypes import ChatRequest, ChatType, PresentationInput
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
from pprint import pformat
import logging

from core.market_size_analysis.test_langgraph import build_business_analysis_graph
import os
import gridfs


from core.market_size_analysis.utils import extract_knowledge_base, get_serializable_response, save_response_to_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

os.makedirs(KNOWLEDGE_BASE_PATH, exist_ok=True)
os.makedirs(FIGURE_PATH, exist_ok=True)
os.makedirs(RESPONSE_PATH, exist_ok=True)

os.makedirs('./rag_base', exist_ok=True)
os.makedirs('./rag_base/chunks', exist_ok=True)
os.makedirs('./rag_base/files', exist_ok=True)
os.makedirs('./rag_base/retrieved_context', exist_ok=True)
os.makedirs('./rag_base/sources', exist_ok=True)

set_llm_cache(InMemoryCache())


app = FastAPI(
    title="Market Flick AI API",
    description="AI-powered business analysis platform",
    version="1.0.0"
)

# Import auth modules
from core.auth.middleware import verify_jwt_token
from core.auth.routes import router as auth_router

# Configure CORS with restricted origins
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Validate environment
if os.getenv("ENVIRONMENT", "development") == "production" and ALLOWED_ORIGINS == ["http://localhost:3000"]:
    logger.warning("⚠️  WARNING: Running in production with development CORS origins. Update ALLOWED_ORIGINS environment variable.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ FIXED: Restricted to configured origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # ✅ FIXED: Explicit HTTP methods
    allow_headers=["Content-Type", "Authorization"],  # ✅ FIXED: Explicit headers
    max_age=600,  # Cache preflight requests for 10 minutes
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
    sector: str = Form(...),
    idea: str = Form(...),
    location: str = Form(...),
    links: list[str] | None = Form(None),
    files: list[UploadFile] | None = Form(None),
    userId : str | None = Form(None)
) -> StreamingResponse:
    """
    Performs AI-powered business analysis with streaming response.
    
    Args:
        sector: Business sector for analysis
        idea: Business idea description
        location: Geographic location
        links: Optional list of reference links
        files: Optional uploaded documents
        userId: User identifier (required)
    
    Raises:
        HTTPException: 400 if userId is missing or empty
    """
    # ✅ FIXED: Input validation with descriptive error messages
    if userId is None or userId.strip() == "":
        logger.warning("Business analysis request received without user ID")
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # ✅ FIXED: Validate input fields
    if not sector or not sector.strip():
        raise HTTPException(status_code=400, detail="Sector is required and cannot be empty")
    
    if not idea or not idea.strip():
        raise HTTPException(status_code=400, detail="Business idea is required and cannot be empty")
    
    if not location or not location.strip():
        raise HTTPException(status_code=400, detail="Location is required and cannot be empty")
    
    # ✅ FIXED: Input sanitization
    sector = sector.strip()
    idea = idea.strip()
    location = location.strip()
    userId = userId.strip()

    try:
        business_input = BusinessAnalysisInput.as_form(
            sector=sector,
            idea=idea,
            location=location,
            files=files,
            links=links
        )
    except ValueError as e:
        logger.error(f"Invalid business input: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    
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
        
        # ✅ FIXED: Error handling for file processing
        try:
            # Save files to MongoDB GridFS
            for file in files:
                try:
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
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    raise HTTPException(status_code=400, detail=f"Error processing file {file.filename}: {str(e)}")

            # Save links to MongoDB
            if links:
                for link in links:
                    try:
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
                    except Exception as e:
                        logger.error(f"Error processing link {link}: {str(e)}")
                        raise HTTPException(status_code=400, detail=f"Error processing link: {str(e)}")

            # Fetch context from uploaded sources
            points = upload_and_fetch_context(
                knowledge_base_id,
                f'Idea: {business_input.idea} - Sector: {business_input.sector} - Location: {business_input.location}',
                sources_object
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing sources for knowledge base {knowledge_base_id}: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing uploaded sources")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Starting business analysis for user {userId} with knowledge base {knowledge_base_id}")
            
            yield json.dumps({
                "key": "start",
                "data": "Analysis started...",
                "status": "success"
            })

            # basic info from the idea
            try:
                title = generate_title(business_input)
            except Exception as e:
                logger.error(f"Error generating title: {str(e)}")
                title = f"{business_input.sector} - {business_input.idea[:50]}"
            
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

            try:
                save_response_to_db(basic_info, knowledge_base_id, user_id=userId, collection_name="basic_info")
            except Exception as e:
                logger.error(f"Error saving basic info to DB: {str(e)}")
                # Don't fail the entire analysis, just log the error

            # Create the graph
            try:
                graph = build_business_analysis_graph()
            except Exception as e:
                logger.error(f"Error building analysis graph: {str(e)}")
                raise

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
                    for node, output in event.items():
                        for key in important_keys:
                            if key in output:
                                try:
                                    yield json.dumps({
                                        "key": key,
                                        "data": get_serializable_response(output[key]),
                                        "status": "success"
                                    })
                                except Exception as e:
                                    logger.error(f"Error serializing response for key {key}: {str(e)}")
                                    yield json.dumps({
                                        "key": key,
                                        "data": f"Error processing {key}",
                                        "status": "error",
                                        "error_detail": str(e)
                                    })

                    # Optional: add a small delay to prevent overwhelming the client
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error in stream processing: {str(e)}", exc_info=True)
                    yield json.dumps({
                        "key": "error",
                        "data": "Error during analysis processing",
                        "status": "error",
                        "error_detail": str(e)
                    })
                    continue

            # Final event to indicate stream completion
            logger.info(f"Analysis completed for knowledge base {knowledge_base_id}")
            yield json.dumps({
                "key": "completion",
                "data": "Analysis completed successfully",
                "status": "success"
            })

        except Exception as e:
            logger.error(f"Unhandled error in business analysis stream: {str(e)}", exc_info=True)
            yield json.dumps({
                "key": "error",
                "data": "An unexpected error occurred during analysis",
                "status": "error",
                "error_detail": str(e)
            })

    # Return a StreamingResponse with the async generator
    return StreamingResponse(generate_stream(), media_type="application/json")




@app.post("/previous-analysis/{knowledge_base_id}")
async def previous_analysis_stream(
    knowledge_base_id: str,
    payload: dict = Body(...)
) -> StreamingResponse:
    """
    Retrieves and streams saved analysis data.
    
    Args:
        knowledge_base_id: ID of the saved analysis
        payload: Request body containing user_id
    """
    # ✅ FIXED: Input validation
    user_id = payload.get("user_id")
    if user_id is None or user_id.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    if not knowledge_base_id or not knowledge_base_id.strip():
        raise HTTPException(status_code=400, detail="Knowledge base ID is required")
    
    user_id = user_id.strip()
    knowledge_base_id = knowledge_base_id.strip()
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Retrieving analysis {knowledge_base_id} for user {user_id}")
            
            yield json.dumps({
                "key": "start",
                "data": "Loading analysis...",
                "status": "success"
            })
            
            # ✅ FIXED: Error handling for database operations
            try:
                saved_responses = get_all_saved_responses(knowledge_base_id, user_id)
            except Exception as e:
                logger.error(f"Error retrieving saved responses: {str(e)}")
                raise HTTPException(status_code=500, detail="Error retrieving analysis")
            
            # Stream the graph execution
            for key, response in saved_responses.items():
                try:
                    for saved_key in important_keys:
                        if saved_key in response:
                            yield json.dumps({
                                "key": saved_key,
                                "data": response[saved_key],
                                "status": "success"
                            })

                    # Optional: add a small delay to prevent overwhelming the client
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(f"Error streaming response: {str(e)}")
                    yield json.dumps({
                        "key": "error",
                        "data": "Error streaming analysis data",
                        "status": "error",
                        "error_detail": str(e)
                    })
                    continue

            # Final event to indicate stream completion
            logger.info(f"Analysis stream completed for {knowledge_base_id}")
            yield json.dumps({
                "key": "completion",
                "data": "Analysis retrieved successfully",
                "status": "success"
            })

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unhandled error in previous analysis stream: {str(e)}", exc_info=True)
            yield json.dumps({
                "key": "error",
                "data": "An unexpected error occurred",
                "status": "error",
                "error_detail": str(e)
            })

    # Return a StreamingResponse with the async generator
    return StreamingResponse(generate_stream(), media_type="application/json")


@app.get("/analyses")
async def get_analyses(user_id : str | None = Query(None)):
    """
    Endpoint to list all saved analyses for a user.
    
    Args:
        user_id: User identifier (required)
    
    Returns:
        List of saved analyses with metadata
    """
    # ✅ FIXED: Input validation
    if user_id is None or user_id.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    user_id = user_id.strip()
    
    try:
        db = get_database()
        collection = db['basic_info']
        # Filter analyses based on user_id from the database
        analyses = collection.find({"user_id": user_id}, {"_id": 0})
        
        return {
            "analyses": list(analyses),
        }

    except Exception as e:
        logger.error(f"Error retrieving analyses for user {user_id}: {str(e)}")
        return {"error": f"Error retrieving analyses: {str(e)}", "analyses": []}

    
@app.post("/chat")
async def chat(chat_request: ChatRequest):
    """
    Chat endpoint for business analysis discussions.
    
    Args:
        chat_request: Chat request with message and context
    """
    # ✅ FIXED: Input validation
    knowledge_base_id = chat_request.id
    user_id = chat_request.user_id
    if user_id is None or user_id.strip() == "":
        raise HTTPException(status_code=400, detail="User ID is required")
    
    if not knowledge_base_id or not knowledge_base_id.strip():
        raise HTTPException(status_code=400, detail="Knowledge base ID is required")
    
    if not chat_request.message or not chat_request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        knowledge_base = extract_knowledge_base(knowledge_base_id)
    except Exception as e:
        logger.error(f"Error extracting knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading analysis context")

    try:
        if chat_request.type == ChatType.CHAT:
            response = chat_with_agent(
                input_text=chat_request.message,
                chat_history=chat_request.chat_history,
                knowledge_base=knowledge_base,
                knowledge_base_id=knowledge_base_id,
                user_id=user_id
            )
        elif chat_request.type == ChatType.WRITE:
            response = chat_write_agent(
                id=chat_request.id,
                input=chat_request.message,
                chat_history=chat_request.chat_history,
                component_keys=chat_request.component_keys,
                knowledge_base=knowledge_base
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid chat type")
        
        return response
    except Exception as e:
        logger.error(f"Error in chat processing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing chat request")


@app.post("/generate-presentation")
async def generate_presentation(presentation_input: PresentationInput):
    """
    Generate a presentation from analysis results.
    
    Args:
        presentation_input: Presentation configuration
    """
    # ✅ FIXED: Input validation
    if not presentation_input.id or not presentation_input.id.strip():
        raise HTTPException(status_code=400, detail="Analysis ID is required")
    
    if not presentation_input.template_name or not presentation_input.template_name.strip():
        raise HTTPException(status_code=400, detail="Template name is required")
    
    try:
        id = presentation_input.id.strip()
        template_name = presentation_input.template_name.strip()
        logger.info(f"Generating presentation for analysis {id} with template {template_name}")
        
        response = create_presentation(id=id, template_name=template_name)

        return {
            "message": "Presentation generated successfully",
            "file_link": f"{BASE_URL}/download-presentation/{id}.pptx"
        }
    except Exception as e:
        logger.error(f"Error generating presentation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error generating presentation")


@app.get("/download-presentation/{id}.pptx")
async def download_file(id: str):
    """
    Download generated presentation file.
    
    Args:
        id: Analysis ID
    """
    # ✅ FIXED: Input validation
    if not id or not id.strip():
        raise HTTPException(status_code=400, detail="Analysis ID is required")
    
    id = id.strip()
    file_path = f"{RESPONSE_PATH}/presentation_{id}.pptx"
    
    try:
        if not os.path.exists(file_path):
            logger.warning(f"Presentation file not found: {file_path}")
            raise HTTPException(status_code=404, detail="Presentation file not found")
        
        return FileResponse(
            path=file_path,
            filename=f"presentation_{id}.pptx",
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading presentation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading file")
  

@app.post("/investor-analysis/{id}")
async def investor_analysis(id: str):
    """
    Perform investor analysis for the business idea.
    
    Args:
        id: Analysis ID
    """
    # ✅ FIXED: Input validation
    if not id or not id.strip():
        raise HTTPException(status_code=400, detail="Analysis ID is required")
    
    id = id.strip()
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            logger.info(f"Starting investor analysis for {id}")
            async for s in get_investor_analysis(id):
                try:
                    message = s["messages"][-1]
                    if isinstance(message, tuple):
                        yield json.dumps({"data": message, "status": "success"})
                    else:
                        yield json.dumps({"data": str(message.pretty_repr()), "status": "success"})
                except Exception as e:
                    logger.error(f"Error processing investor analysis message: {str(e)}")
                    yield json.dumps({"data": "Error processing analysis", "status": "error", "error_detail": str(e)})
        
        except Exception as e:
            logger.error(f"Error in investor analysis stream: {str(e)}", exc_info=True)
            yield json.dumps({"event": "error", "data": "Analysis error", "error_detail": str(e)})

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
    }
    
    return StreamingResponse(generate_stream(), media_type="application/json", headers=headers)


@app.get("/investor-profiles/{id}")
async def investor_profiles(id: str):
    """
    Retrieve investor profiles for an analysis.
    
    Args:
        id: Analysis ID
    """
    # ✅ FIXED: Input validation
    if not id or not id.strip():
        raise HTTPException(status_code=400, detail="Analysis ID is required")
    
    id = id.strip()
    
    try:
        logger.info(f"Retrieving investor profiles for {id}")
        response = load_response_from_db(f"investors_and_companies_{id}")
        return response
    except Exception as e:
        logger.error(f"Error loading investor profiles: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading investor profiles")


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    try:
        db = get_database()
        db.command('ping')
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
