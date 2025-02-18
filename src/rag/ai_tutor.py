from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


class RAG:
    def __init__(self, system_prompt: str, llm, retriever):
        """
        Base class for creating a Retrieval-Augmented Generation (RAG) chain.

        Args:
            system_prompt (str): The system prompt template.
            llm: The language model to use.
            retriever: The retriever to use for context retrieval.
        """
        self.system_prompt = system_prompt + '\n ------ \n{context}'

        # Set up the prompt for the QA chain
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}")
            ]
        )

        self.llm = llm

        # Create the RAG chain
        self.chain = create_stuff_documents_chain(llm, self.prompt)
        self.rag_chain = create_retrieval_chain(retriever, self.chain)

    def clean_query_with_llm(self, question: str) -> str:
        """
        Use the LLM to clean and normalize the user's question.

        Args:
            question (str): The user's question.

        Returns:
            str: The cleaned and normalized question.
        """
        prompt = f"""
        You are a helpful assistant that cleans and normalizes user queries in spanish for a RAG system.
        Your task is to reformat the following query to make it more suitable for retrieval and generation:
        - Correct any spelling or grammatical errors.
        - Remove unnecessary words or phrases.
        - Clarify ambiguous terms.
        - Ensure the query is concise and clear.

        ----
        Example:
        query : qué es un array de direcciones
        cleaned query: array de direcciones

        ----

        Original query: "{question}"

        Cleaned query:
        """
        clean_query = self.llm.invoke(prompt)
        return clean_query.content.strip()

    def answer_question(self, question: str):
        """
        Use the RAG chain to answer a question.

        Args:
            question (str): The question to answer.

        Returns:
            str: The response from the RAG chain.
        """
        clean_question = self.clean_query_with_llm(question)
        response = self.rag_chain.invoke({"input": clean_question})
        return response


class AITutor(RAG):
    def __init__(self, llm, retriever):
        """
        Specialized AI tutor class for C# programming.

        Args:
            llm: The language model to use.
            retriever: The retriever to use for context retrieval.
        """
        # Define the specific system prompt for the AI tutor
        system_prompt = '''
        You are an AI tutor specialized in C# programming, dedicated to providing clear, thorough, and step-by-step explanations.
        Your primary goal is to simplify complex concepts into easy-to-understand terms, maintaining a warm and conversational tone.

        - Your responses must be based **exclusively** on the content from the provided material and its examples.
        - If the question is not covered in the material, politely explain that the answer is not available in the provided document.
        - Respond **in Spanish**, ensuring your explanation is clear and beginner-friendly.

        At the end of each response:
        1. Include a reference to the source (document name) and the relevant page numbers.
        2. Use proper formatting for a Telegram message, ensuring any included code is written in a block like this:

        ```csharp
        Console.WriteLine("Hello world");
        ```

        Keep your answers concise, informative, and engaging, ensuring students feel supported in their learning journey.
        Do not add any information beyond what the material provides.
        '''
        super().__init__(system_prompt, llm, retriever)
