from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from config.settings import LLM_PROVIDER, GROQ_API_KEY


class LLMFactory:

    @staticmethod
    def behavioral_llm():
        if LLM_PROVIDER == "groq":
            return ChatGroq(
                model="llama-3.1-8b-instant", temperature=0, groq_api_key=GROQ_API_KEY
            )

        # Local configuration for behavioral analysis
        return ChatOllama(
            model="qwen3.6:35b",
            temperature=0,
            num_ctx=8192,  # Ensure full prompt fits comfortably
        )

    @staticmethod
    def reasoning_llm():
        if LLM_PROVIDER == "groq":
            return ChatGroq(
                model="llama-3.1-8b-instant", temperature=0, groq_api_key=GROQ_API_KEY
            )

        # DeepSeek-R1 is fantastic for pure reasoning/compliance documents
        return ChatOllama(
            model="qwen3.6:35b",
            temperature=0.6,  # R1 performs better with a slight temperature
            num_ctx=8192,
        )

    @staticmethod
    def graph_llm():
        if LLM_PROVIDER == "groq":
            return ChatGroq(
                model="llama-3.1-8b-instant", temperature=0, groq_api_key=GROQ_API_KEY
            )

        # CRITICAL CHANGE: Swapped from deepseek-r1 to llama3.1
        # because this node MUST support tool-calling (query_graph_database)
        return ChatOllama(
            model="qwen3.6:35b",  # Or use 'qwen2.5-coder' if you have it downloaded
            temperature=0,  # Must be 0 for rigid Cypher syntax generation
            num_ctx=8192,  # Essential for housing the schema + few-shots
        )
