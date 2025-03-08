"""
LLM 래퍼 모듈
- LoggingChatOpenAI: 로깅 기능이 추가된 ChatOpenAI 래퍼
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from chatbot_modules.logging_utils import log_llm_communication, OPENAI_API_KEY, check_api_key

class LoggingChatOpenAI(ChatOpenAI):
    """로깅 기능이 추가된 ChatOpenAI 래퍼 클래스"""
    
    def __init__(self, **kwargs):
        """API 키를 환경 변수에서 가져와 초기화합니다."""
        # API 키 확인
        check_api_key()
        
        # 기본 설정과 사용자 정의 설정을 병합
        default_params = {
            "api_key": OPENAI_API_KEY,
            "temperature": 0.7,
            "model_name": "gpt-3.5-turbo",
        }
        # kwargs에 있는 설정으로 기본 설정을 덮어씁니다.
        for key, value in kwargs.items():
            default_params[key] = value
            
        # 부모 클래스 초기화
        super().__init__(**default_params)
    
    def invoke(self, input, config=None, **kwargs):
        """LLM 호출 및 로깅"""
        # 입력 메시지 로깅
        request_data = self._format_for_logging(input)
        
        # 부모 클래스의 invoke 메서드 호출
        response = super().invoke(input, config=config, **kwargs)
        
        # 응답 로깅
        response_data = self._format_for_logging(response)
        
        # LLM 통신 로깅
        try:
            log_llm_communication(request_data, response_data, source=self.__class__.__name__)
        except Exception as e:
            print(f"로깅 중 오류 발생: {e}")
        
        return response
    
    def _format_for_logging(self, data):
        """로깅을 위한 데이터 형식 변환"""
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif isinstance(data, list):
            return [self._format_for_logging(item) for item in data]
        elif hasattr(data, "content") and callable(getattr(data, "content", None)):
            # 일부 LangChain 객체는 content가 메서드임
            try:
                return {"content": str(data.content())}
            except:
                return {"content": str(data)}
        elif hasattr(data, "content"):
            # Message 객체 처리
            return self._message_to_dict(data)
        elif isinstance(data, dict):
            return {k: self._format_for_logging(v) for k, v in data.items()}
        else:
            # 직렬화할 수 없는 객체는 문자열로 변환
            try:
                # __dict__ 속성 시도
                if hasattr(data, "__dict__"):
                    return {"type": data.__class__.__name__, "data": str(data.__dict__)}
                # to_json, to_dict 등의 메서드 시도
                elif hasattr(data, "to_json"):
                    return data.to_json()
                elif hasattr(data, "to_dict"):
                    return data.to_dict()
                else:
                    return {"type": data.__class__.__name__, "data": str(data)}
            except:
                return {"type": data.__class__.__name__, "data": "Unable to serialize"}
    
    def _message_to_dict(self, message):
        """Message 객체를 딕셔너리로 변환"""
        if hasattr(message, "content") and hasattr(message, "type"):
            return {"role": message.type, "content": message.content}
        else:
            return {"role": "unknown", "content": str(message)} 