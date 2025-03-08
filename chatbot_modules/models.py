"""
데이터 모델 정의 모듈
- Persona: 챗봇 페르소나 정의
- ConversationContext: 대화 맥락 모델
- UserInformation: 사용자 정보 모델
"""

from typing import Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field

# 페르소나 정의
class Persona(TypedDict):
    """챗봇의 페르소나를 정의하는 클래스"""
    name: str
    description: str
    system_prompt: str
    greeting: str

# 대화 맥락 모델
class ConversationContext(BaseModel):
    """대화 맥락을 관리하는 모델"""
    main_topics: List[str] = Field(default_factory=list, description="현재 대화의 주요 주제들")
    current_context: str = Field("", description="현재 대화의 요약된 맥락")
    pending_questions: List[str] = Field(default_factory=list, description="아직 대답하지 않은 사용자의 질문들")
    references: Dict[str, str] = Field(default_factory=dict, description="대화 중 언급된 참조 정보(예: 웹사이트, 책 등)")
    last_update_time: str = Field("", description="마지막으로 맥락이 업데이트된 시간")

# 사용자 정보 모델
class UserInformation(BaseModel):
    """사용자 정보를 저장하는 모델"""
    name: Optional[str] = Field(None, description="사용자의 이름")
    age: Optional[int] = Field(None, description="사용자의 나이")
    occupation: Optional[str] = Field(None, description="사용자의 직업")
    location: Optional[str] = Field(None, description="사용자의 위치 또는 거주지")
    interests: List[str] = Field(default_factory=list, description="사용자의 관심사 목록")
    preferences: Dict[str, str] = Field(default_factory=dict, description="사용자의 선호도 (카테고리: 선호도)")
    goals: List[str] = Field(default_factory=list, description="사용자의 목표 목록")
    family: Dict[str, str] = Field(default_factory=dict, description="사용자의 가족 정보 (관계: 이름)")
    contact_info: Optional[str] = Field(None, description="사용자의 연락처 정보")

# 친구 페르소나 설정
FRIEND_PERSONA: Persona = {
    "name": "친구",
    "description": "사용자와 친근하게 대화하는 친구 같은 챗봇",
    "system_prompt": """
    당신은 사용자의 친한 친구처럼 대화하는 AI 챗봇입니다. 친근하고 캐주얼한 말투를 사용하고, 
    사용자가 편안하게 이야기할 수 있도록 공감과 이해를 보여주세요. 
    사용자의 관심사, 취미, 감정에 관심을 보이고 자연스러운 대화 흐름을 유지하세요.
    
    대화중에 사용자에 대한 중요한 정보를 기억하고, 적절한 순간에 이전 대화 내용을 참조하여 
    일관성 있는 대화를 이어나가세요.
    """,
    "greeting": "안녕! 오늘 어떻게 지내?"
} 