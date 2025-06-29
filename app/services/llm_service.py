from groq import Groq
from app.core.config import settings


class GroqClient:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def generate_response(self, model: str, system_prompt: str, user_query: str, context: str, temp: float, top_p: float) -> str:
        """
        Generates a response from the Groq API using a formatted prompt.
        
        Args:
            model: The Groq model to use for generation
            system_prompt: The system prompt to set the context
            user_query: The user's query
            context: Additional context for the query
            temp: Temperature for response generation
            top_p: Top-p sampling parameter
            
        Returns:
            Generated response string or error message
        """
        formatted_prompt = (
            f"Context: {context}\n\n"
            f"Based on the context above, please answer the following query.\n"
            f"Query: {user_query}"
        )
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": formatted_prompt,
                    },
                ],
                model=model,
                temperature=temp,
                top_p=top_p,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return "Sorry, I encountered an error while trying to generate a response."


llm_client = GroqClient()