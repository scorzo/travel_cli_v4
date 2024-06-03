# generic_agent.py

from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain_core.agents import AgentActionMessageLog, AgentFinish
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import json
import sys
from termcolor import colored

class GenericAgent:
    def __init__(self, model_name="gpt-4o", pydantic_model=None, tools=None):
        self.model_name = model_name
        self.pydantic_model = pydantic_model
        self.tools = tools or []
        self._validate_tools()

    def _validate_tools(self):
        for tool in self.tools:
            if not hasattr(tool, 'name') or not hasattr(tool, 'description') or not hasattr(tool, 'args'):
                raise ValueError(f"Invalid tool: {tool}. Each tool must have 'name', 'description', and 'args' attributes.")


    def create_agent(self):
        agent_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        llm = ChatOpenAI(model=self.model_name, temperature=0)
        tools_and_model = self.tools + [self.pydantic_model]
        llm_with_tools = llm.bind_functions(tools_and_model)


        agent = (
                {
                    "input": lambda x: x["input"],
                    # Format agent scratchpad from intermediate steps
                    "agent_scratchpad": lambda x: format_to_openai_function_messages(
                        x["intermediate_steps"]
                    ),
                }
                | agent_prompt
                | llm_with_tools
                | self.parse
        )

        return agent

    def generate_response(self, prompt):

        # Create and use the agent
        agent = self.create_agent()
        agent_executor = AgentExecutor(tools=self.tools, agent=agent)

        response = agent_executor.invoke(
            {"input": prompt},
            return_only_outputs=True,
        )

        return response

    def parse(self, output):
        # If no function was invoked, return to user
        if "function_call" not in output.additional_kwargs:
            print(colored("No function call detected in the output. Attempting to parse output content as JSON.", "blue"))
            try:
                # Try to parse the output content as JSON
                output_dict = json.loads(output.content)
                # If successful, return the JSON dictionary
                print(colored("Successfully parsed JSON content.", "blue"))
                return AgentFinish(return_values=output_dict, log=output.content)
            except json.JSONDecodeError as e:
                # If parsing fails, print the JSON error
                print(colored(f"JSON decode error: {e}", "red"))
                sys.exit()

        # Parse out the function call
        print(colored("Function call detected. Extracting function name and arguments.", "yellow"))
        function_call = output.additional_kwargs["function_call"]
        name = function_call["name"]
        inputs = json.loads(function_call["arguments"])
        print(colored(f"Function name: {name}", "yellow"))
        print(colored(f"Function inputs: {inputs}", "yellow"))

        # If the function corresponding to pydantic_model was invoked, return to the user with the function inputs
        if name != self.pydantic_model.__name__:
            print(colored("Function name does not match pydantic model. Returning agent action.", "yellow"))
            return AgentActionMessageLog(
                tool=name, tool_input=inputs, log="", message_log=[output]
            )
        else:
            print(colored("Function name matches pydantic model. Returning function inputs to the user.", "green"))
            return AgentFinish(return_values=inputs, log=str(function_call))
