#==============================================
# 레그 체이닝 참고 코드
# 검색 > 딕셔너리 > 등등 
#============================================== 


# store = {}

# def get_session_history(session_id):
#     if session_id not in store:
#         store[session_id] = ChatMessageHistory()
#     return store[session_id]

# def get_retriever():
#     embedding = OpenAIEmbeddings(model="text-embedding-3-large")
#     index_name = 'tax-index'
#     database = PineconeVectorStore.from_existing_index(index_name=index_name, embedding=embedding)
#     retriever = database.as_retriever(search_kwargs={'k' : 4})
#     return retriever

# def get_history_aware_retriever():
#     llm = get_llm()
#     retriever = get_retriever()

#     contextualize_q_system_prompt = (
#         "Given a chat history and the latest user question "
#         "두괄식으로 대답해주세요"
#         "which might reference context in the chat history, "
#         "formulate a standalone question which can be understood "
#         "without the chat history. Do NOT answer the question, "
#         "just reformulate it if needed and otherwise return it as is."
#     )

#     contextualize_q_prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", contextualize_q_system_prompt),
#             MessagesPlaceholder("chat_history"),
#             ("human", "{input}"),
#         ]
#     )
#     history_aware_retriever = create_history_aware_retriever(
#         llm, retriever, contextualize_q_prompt
#     )
#     return history_aware_retriever

# def get_llm(model="gpt-4o"):
#     llm = ChatOpenAI(model=model)  
#     return llm

# def get_dictionary_chain():
#     dictionary = ["사람을 나타내는 표현 -> 거주자"]
#     llm = get_llm()
#     prompt = ChatPromptTemplate.from_template(f"""
#         사용자의 질문을 보고, 우리의 사전을 참고해서 사용자의 질문을 변경해주세요.
#         만약 변경할 필요가 없다고 판단되면, 사용자의 질문을 변경하지 않아도 됩니다.
#         사전: {dictionary}

#         질문: {{question}}
#     """)

#     dictionary_chain = prompt | llm | StrOutputParser()

#     return dictionary_chain

# def get_rag_chain():
#     llm = get_llm()    

#     example_prompt = ChatPromptTemplate.from_messages(
#         [
#             ("human", "{input}"),
#             ("ai", "{answer}"),
#         ]
#     )

#     few_shot_prompt = FewShotChatMessagePromptTemplate(
#         example_prompt=example_prompt,
#         examples=answer_examples,
#         input_variables=["input"]
#     )

#     system_prompt = (
#         "2-3 문장정도의 짧은 내용의 답변을 원합니다."
#         "\n\n"
#         "{context}"
#     )
#     qa_prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", system_prompt),
#             few_shot_prompt,
#             MessagesPlaceholder("chat_history"),
#             ("human", "{input}"),
#         ]
#     )
#     history_aware_retriever = get_history_aware_retriever()
#     question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

#     rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

#     conversation_rag_chain = RunnableWithMessageHistory(
#         rag_chain, 
#         get_session_history,
#         input_messages_key="input",
#         history_messages_key="chat_history",
#         output_messages_key="answer",
#     ).pick("answer")

#     return conversation_rag_chain

# def get_ai_response(user_message):
#     dictionary_chain = get_dictionary_chain()
#     rag_chain = get_rag_chain()
#     tax_chain = {"input":dictionary_chain} | rag_chain
#     ai_response = tax_chain.stream(
#         {
#             "question": user_message
#         },
#         config={
#             "configurable": {"session_id": "123"}
#         }
#     )

#     return ai_response