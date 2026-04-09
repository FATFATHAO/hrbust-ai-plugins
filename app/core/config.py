from langchain_community.llms import Ollama

class Settings:
    PROJECT_NAME: str = "HRBUST AI Plugins Microservice"
    
    @property
    def local_llm(self):
        # 通过LangChain桥接大模型
        return Ollama(
            model="qwen2.5:32b",
            base_url="http://172.17.0.1:11434"
        )

settings = Settings()
