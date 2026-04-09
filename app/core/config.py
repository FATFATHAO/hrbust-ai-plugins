from pandasai.llm import Ollama

class Settings:
    PROJECT_NAME: str = "HRBUST AI Plugins Microservice"
    
    # 全局大模型单例
    @property
    def local_llm(self):
        return Ollama(
            model="qwen2.5:32b",
            base_url="http://172.17.0.1:11434"
        )

settings = Settings()
