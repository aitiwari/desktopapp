from autogen import AssistantAgent, UserProxyAgent
import toml
from autogen import AssistantAgent, UserProxyAgent

class Chat:
    def __init__(self,input_message):
        self.input_message = input_message
    
    def call_ai_agent(self):
        # Load the configuration from the TOML file
        config = toml.load("./prompt.toml")
        agent_description = config["summarizer_agent"]["description"]



        config_list = [
            {
                "model": "deepseek-r1:1.5b",
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
            }
        ]

        assistant = AssistantAgent("assistant", llm_config={"config_list": config_list},description=agent_description)
        input_message = f'Summarize below content in markdown format : {self.input_message}'
        user_proxy = UserProxyAgent("user_proxy", code_execution_config= False,human_input_mode = 'NEVER')
        res = user_proxy.initiate_chat(assistant, message=input_message,max_turns =1)
        return res.summary