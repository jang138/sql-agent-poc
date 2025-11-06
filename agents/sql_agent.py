"""
SQL Agent 생성 및 관리 모듈
"""

from langchain_upstage import ChatUpstage
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from config import settings
from database import db_manager
from utils import search_table_metadata


class SQLAgentManager:
    """SQL Agent 관리 클래스"""

    def __init__(self):
        self.llm = None
        self.agent = None
        self.db = None

    def initialize(self):
        """Agent 초기화"""
        # LLM 초기화
        self.llm = ChatUpstage(
            api_key=settings.UPSTAGE_API_KEY,
            model=settings.MODEL_NAME,
            temperature=settings.TEMPERATURE,
        )
        print(f"✅ LLM 초기화 완료: {settings.MODEL_NAME}")

        # DB 연결
        self.db = db_manager.get_db()

        # SQL Agent 생성
        self.agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
            handle_parsing_errors=True,
        )
        print("✅ SQL Agent 생성 완료")

        return self.agent

    def query(self, question: str) -> dict:
        """
        자연어 질문을 SQL로 변환하여 실행

        Args:
            question: 자연어 질문

        Returns:
            dict: {
                "question": 질문,
                "answer": 답변,
                "success": 성공 여부,
                "error": 에러 메시지 (있을 경우)
            }
        """
        if self.agent is None:
            self.initialize()

        try:
            print(f"\n{'='*60}")
            print(f"❓ 질문: {question}")
            print(f"{'='*60}")

            result = self.agent.invoke({"input": question})

            return {
                "question": question,
                "answer": result.get("output", ""),
                "success": True,
                "error": None,
            }

        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            return {
                "question": question,
                "answer": None,
                "success": False,
                "error": str(e),
            }

    def get_agent(self):
        """Agent 인스턴스 반환"""
        if self.agent is None:
            self.initialize()
        return self.agent


# 전역 Agent 매니저 인스턴스
sql_agent_manager = SQLAgentManager()
