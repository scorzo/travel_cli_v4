from calendar_package.list_calendar_events import ListEventsTool
from .models import PromptsList
from datetime import date
import json
from generic_agent import GenericAgent

def generate_prompts_from_model(prompt, personal_preferences=None, model_name="gpt-4o", pydantic_model=PromptsList, tools=[ListEventsTool()]):
    """
    Generates a list of prompts based on a user-provided seed prompt and optional personal preferences
    using a specified language model.

    Args:
        prompt (str): The seed prompt to send to the language model.
        personal_preferences (dict, optional): A dictionary of user personal preferences that can
                                               guide the generation of prompts.
        model_name (str): The name of the model to use, defaults to 'gpt-4o'.

    Returns:
        dict: A dictionary representing the dynamically generated list of prompts.

    Example:
        >>> from generate_prompts import generate_prompts_from_model
        >>> import json
        >>> user_preferences = {'interests': ['cuisine', 'historic sites'], 'location': 'Europe'}
        >>> dynamic_prompts = generate_prompts_from_model("Generate 3 travel itinerary prompts", user_preferences)
        >>> print(json.dumps(dynamic_prompts, indent=2))
    """
    # Enhance prompt with personal preferences if provided
    if personal_preferences:
        enhanced_prompt = f"{prompt} based on preferences {json.dumps(personal_preferences)}. Exclude dates that are not available based on the calendar."
    else:
        enhanced_prompt = f"{prompt}. Exclude dates that are not available based on the calendar."

    # Create an instance of GenericAgent
    generic_agent = GenericAgent(model_name=model_name, pydantic_model=pydantic_model, tools=tools)

    append_this = "  Respond with final answer using PromptsList output format and only the PromptsList output format."

    # Append the string
    enhanced_prompt += append_this

    # Generate the response using the agent
    response = generic_agent.generate_response(enhanced_prompt)

    # response_dict = response.dict()
    # # Ensure all dates are converted to strings
    # if 'created_at' in response_dict and isinstance(response_dict['created_at'], date):
    #     response_dict['created_at'] = response_dict['created_at'].strftime("%Y-%m-%d")

    return response

# Example usage
if __name__ == "__main__":
    print("Generated Prompts from Model:")
    response_dict = generate_prompts_from_model("Generate 3 travel itinerary prompts")
    print(json.dumps(response_dict, indent=2))
