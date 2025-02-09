import asyncio
from langchain_ollama import ChatOllama
from browser_use import Agent
from pydantic import SecretStr


# Initialize the model
#llm=ChatOllama(model="deepseek-r1:1.5b", num_ctx=32000)
llm=ChatOllama(model="qwen2.5:latest")

# # Create agent with the model
# agent = Agent(
#     task="Your task here",
#     llm=llm
# )


async def main():
    agent = Agent(
        task="open amazon site and search for iphones model. add to order list",
        llm=llm,
        use_vision=False
    )
    result = await agent.run()
    print(result)

asyncio.run(main())