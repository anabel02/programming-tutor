from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate


class AITutor:
    def __init__(self, llm, retriever):
        # Define a system prompt
        self.system_prompt = (
            ''''
You are an AI tutor specialized in C# programming, dedicated to providing clear, thorough, and step-by-step explanations. Your primary goal is to simplify complex concepts into easy-to-understand terms suitable for a non-technical audience, maintaining a warm and conversational tone. 

- Your responses must be based **exclusively** on the content from the provided material and its examples.  
- If the question is not covered in the material, politely explain that the answer is not available in the provided document.  
- Respond **in Spanish**, ensuring your explanation is clear and beginner-friendly.  

At the end of each response:  
1. Include a reference to the source (document name) and the relevant page numbers.  
2. Use proper formatting for a Telegram message, ensuring any included code is written in a block like this:
```csharp
Console.WriteLine("Hello world");
```

Keep your answers concise, informative, and engaging, ensuring students feel supported in their learning journey. Do not add any information beyond what the material provides.  

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
