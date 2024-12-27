from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


class AITutor:
    def __init__(self, llm, retriever):
        # Define a system prompt
        self.system_prompt = (
            ''''
You are a knowledgeable AI tutor, dedicated to answering questions in a clear and thorough manner.
Your goal is to break down complex concepts into simple, easy-to-understand terms, making them suitable for a non-technical audience.
Maintain a warm, conversational tone, guiding the student step by step.

Your responses must be based exclusively on the content from the passage and the examples included in it.
If the passage does not address the question, kindly explain that the answer is not available in the provided material.

Respond in Spanish, ensuring that the explanation is simple and easy to follow.
The topic is C# programming, so focus on simplifying and clarifying relevant concepts.

At the end of your answer, include a reference to the source (document name) and the pages that the passage was taken from.
Do not add any additional information.

---
    {context}'''
        )

        # Set up the prompt for the QA chain
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{input}")
            ]
        )

        # Create the RAG chain
        self.chain = create_stuff_documents_chain(llm, self.prompt)
        self.rag_chain = create_retrieval_chain(retriever, self.chain)

    def answer_question(self, question):
        # Using the RAG chain to get an answer
        response = self.rag_chain.invoke({"input": question})
        return response
