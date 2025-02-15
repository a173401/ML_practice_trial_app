from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Response
from lib.app.verifiers import only_admin, verify_token
from lib.app.services import get_agent_service
from lib.app.models import AgentCreate, AgentUpdate
from lib.models.agent_dto import Agent, AgentType
from lib.database.agents_repository import ExceptionAgentExists, ExceptionAgentNotFound
from lib.agent_service import AgentService
from typing import Annotated, List

router = APIRouter(tags=["Agent"], dependencies=[Depends(verify_token)])


@router.post("/agent", response_model=Agent, dependencies=[Depends(only_admin)])
async def create_agent(agent_create_request: AgentCreate,
                       agent_service: Annotated[AgentService, Depends(get_agent_service)]):
    try:
        agent = agent_service.create_agent(agent_create_request.name, 
                                        agent_create_request.system_context, 
                                        agent_create_request.model, 
                                        agent_create_request.agent_type, 
                                        agent_create_request.cost_per_token, 
                                        agent_create_request.version)
    except ExceptionAgentExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Agent already exists",
        )
    return agent

@router.get("/list", response_model=List[Agent])
async def list_agents(agent_service: Annotated[AgentService, Depends(get_agent_service)]):
    return agent_service.list_agents()


@router.delete("/{agent_id}", dependencies=[Depends(only_admin)])
async def delete_agent(agent_id: UUID, 
                       agent_service: Annotated[AgentService, Depends(get_agent_service)]):
    agent = agent_service.get_agent_by_id(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    agent_service.delete_agent(agent)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{agent_id}", response_model=Agent, dependencies=[Depends(only_admin)])
async def update_agent(agent_id: UUID, 
                       agent_service: Annotated[AgentService, Depends(get_agent_service)],
                       agent_update_request: AgentUpdate):
    updated_agent = agent_service.update_agent(agent_id, 
                                               agent_update_request.name, 
                                               agent_update_request.system_context, 
                                               agent_update_request.model, 
                                               agent_update_request.agent_type, 
                                               agent_update_request.cost_per_token)
    return updated_agent

@router.get("/{agent_id}", response_model=Agent)
async def get_agent_by_id(agent_id: UUID, 
                          agent_service: Annotated[AgentService, Depends(get_agent_service)]):
    try:
        agent = agent_service.get_agent_by_id(agent_id)
    except ExceptionAgentNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent

