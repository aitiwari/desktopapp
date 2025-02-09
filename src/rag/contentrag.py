from typing_extensions import Annotated

import autogen
from autogen import AssistantAgent
from autogen.agentchat.contrib.retrieve_user_proxy_agent import RetrieveUserProxyAgent
from autogen import AssistantAgent, UserProxyAgent
import toml
from autogen import AssistantAgent, UserProxyAgent

from src.rag.myretrieveuserproxyagent import MyRetrieveUserProxyAgent


# from src.rag.myretrieveuserproxyagent import MyRetrieveUserProxyAgent


config_list = [
        {
            "model": "deepseek-r1:1.5b",
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
        }
    ]

# print("LLM models: ", [config_list[i]["model"] for i in range(len(config_list))])
PROBLEM = ''

def termination_msg(x):
    return isinstance(x, dict) and "TERMINATE" == str(x.get("content", ""))[-9:].upper()


llm_config = {"config_list": config_list, "timeout": 60, "temperature": 0.8, "seed": 1234}

boss = autogen.UserProxyAgent(
    name="Boss",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    code_execution_config=False,  # we don't want to execute code in this case.
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    description="The boss who ask questions and give tasks.",
)

boss_aid = MyRetrieveUserProxyAgent(
    name="Boss_Assistant",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    max_consecutive_auto_reply=3,
    code_execution_config=False,  # we don't want to execute code in this case.
    description="Assistant who has extra content retrieval power for solving difficult problems.",
    retrieve_config={
        "chunk_token_size": 1000,
        "model": config_list[0]["model"],
        "collection_name": "groupchat",
        "get_or_create": True,
    }
    
)

coder = AssistantAgent(
    name="Senior_Python_Engineer",
    is_termination_msg=termination_msg,
    system_message="You are a senior python engineer, you provide python code to answer questions. Reply `TERMINATE` in the end when everything is done.",
    llm_config=llm_config,
    description="Senior Python Engineer who can write code to solve problems and answer questions.",
)

pm = autogen.AssistantAgent(
    name="Product_Manager",
    is_termination_msg=termination_msg,
    system_message="You are a product manager. Reply `TERMINATE` in the end when everything is done.",
    llm_config=llm_config,
    description="Product Manager who can design and plan the project.",
)

reviewer = autogen.AssistantAgent(
    name="Code_Reviewer",
    is_termination_msg=termination_msg,
    system_message="You are a code reviewer. Reply `TERMINATE` in the end when everything is done.",
    llm_config=llm_config,
    description="Code Reviewer who can review the code.",
)




def _reset_agents():
    boss.reset()
    boss_aid.reset()
    coder.reset()
    pm.reset()
    reviewer.reset()


def rag_chat_content(input_message,collection_name):
    # Load the configuration from the TOML file
    config = toml.load("./prompt.toml")
    agent_description = config["summarizer_agent"]["description"]


    boss_aid = MyRetrieveUserProxyAgent(
    name="Boss_Assistant",
    is_termination_msg=termination_msg,
    human_input_mode="NEVER",
    default_auto_reply="Reply `TERMINATE` if the task is done.",
    max_consecutive_auto_reply=3,
    code_execution_config=False,  # we don't want to execute code in this case.
    description="Assistant who has extra content retrieval power for solving difficult problems.",
    retrieve_config={
        "chunk_token_size": 1000,
        "model": config_list[0]["model"],
        "collection_name": collection_name,
        "get_or_create": True,
        "task":'qa'
    }
    
)
    
    
    assistant = AssistantAgent("assistant", llm_config={"config_list": config_list},system_message=agent_description)
    input_message = f'Summarize below content in markdown format : {input_message}'
    user_proxy = UserProxyAgent("user_proxy", code_execution_config= False,human_input_mode = 'NEVER')
        
    _reset_agents()
    groupchat = autogen.GroupChat(
        agents=[boss_aid,assistant], messages=[], max_round=2, speaker_selection_method="round_robin"
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with boss_aid as this is the user proxy agent.
    result = boss_aid.initiate_chat(
        manager,
        message=boss_aid.message_generator,
        problem=input_message,
        n_results=8,
    )
    print(result.summary)
    return result.summary


def norag_chat():
    _reset_agents()
    groupchat = autogen.GroupChat(
        agents=[boss, pm, coder, reviewer],
        messages=[],
        max_round=12,
        speaker_selection_method="auto",
        allow_repeat_speaker=False,
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the boss as this is the user proxy agent.
    boss.initiate_chat(
        manager,
        message=PROBLEM,
    )


def call_rag_chat():
    _reset_agents()

    # In this case, we will have multiple user proxy agents and we don't initiate the chat
    # with RAG user proxy agent.
    # In order to use RAG user proxy agent, we need to wrap RAG agents in a function and call
    # it from other agents.
    def retrieve_content(
        message: Annotated[
            str,
            "Refined message which keeps the original meaning and can be used to retrieve content for code generation and question answering.",
        ],
        n_results: Annotated[int, "number of results"] = 3,
    ) -> str:
        boss_aid.n_results = n_results  # Set the number of results to be retrieved.
        _context = {"problem": message, "n_results": n_results}
        ret_msg = boss_aid.message_generator(boss_aid, None, _context)
        return ret_msg or message

    boss_aid.human_input_mode = "NEVER"  # Disable human input for boss_aid since it only retrieves content.

    for caller in [pm, coder, reviewer]:
        d_retrieve_content = caller.register_for_llm(
            description="retrieve content for code generation and question answering.", api_style="function"
        )(retrieve_content)

    for executor in [boss, pm]:
        executor.register_for_execution()(d_retrieve_content)

    groupchat = autogen.GroupChat(
        agents=[boss, pm, coder, reviewer],
        messages=[],
        max_round=12,
        speaker_selection_method="round_robin",
        allow_repeat_speaker=False,
    )

    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    # Start chatting with the boss as this is the user proxy agent.
    boss.initiate_chat(
        manager,
        message=input_message,
    )
    
    
    
if __name__ == "__main__":
    input_message = 'what is gdp'
    collection_name =  'gdp'
    input_message = input_message
    rag_chat_content(input_message,collection_name)
      

    
    