from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import JsonResponse
from django import forms
from django.urls import reverse
from django.utils import timezone
from .models import Chats

from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory , ChatMessageHistory 

import pandas as pd
import json

# Create your views here.

# Chroma 데이터베이스 초기화 - 웹크롤링한 데이터까지 DB 구축
embeddings = OpenAIEmbeddings(model = "text-embedding-ada-002")
database = Chroma(persist_directory = "./database", embedding_function = embeddings)

def index(request):
    # 처음 페이지 요청 시 작동하도록
    if request.method == 'GET':
        # 대화 메모리 생성 (이전 대화를 잊으려할 때 사용)
        memory = ConversationBufferMemory(memory_key="chat_history", input_key="question", output_key="answer",
                                          return_messages=True)
        save_memory_to_session(request, memory)
        
        # 세션에 대화 저장하기
        if 'conversation' not in request.session:
            request.session['conversation'] = []
        
        return render(request, 'selfchatgpt/index.html')
    # 페이지에서 값 입력받은 후 추가로 입력되는 데이터에 따라서 입력이 바뀌는 부분
    if request.method == 'POST':
        #post로 받은 question (index.html에서 name속성이 question인 input태그의 value값)을 가져옴
        query = request.POST.get('question')
        
        retriever = database.as_retriever(search_kwargs={"k": 3})
        chat = ChatOpenAI(model="gpt-3.5-turbo")
        
        # 세션 내에 생성된 memory 불러오기
        memory = load_memory_from_session(request)
        
        # ConversationalRetrievalQA 체인 생성
        qa = ConversationalRetrievalChain.from_llm(llm=chat, retriever=retriever, memory=memory,
                                                   return_source_documents=True,  output_key="answer")

        result = qa(query)
        answer = result['answer']
        
        # 현재 세션에서 대화 불러오기
        conversation = request.session.get('conversation', [])
        # 유저 메시지를 대화에 추가
        conversation.append({"role": "user", "content": query})
        # 대화 내용 세션에 저장
        if 'conversation' not in request.session:
            request.session['conversation'] = []
        request.session['conversation'].append({"role": "user", "content": query})
        request.session['conversation'].append({"role": "assistant", "content": answer})
        request.session.modified = True
        
        username = "none"
        if request.user.is_authenticated:
            username = request.user.username
        chat = Chats.objects.create(question=query, result=answer, username=username)

        # result.html에서 사용할 context
        context = {
            'question': query,
            'result': result["answer"],
        }

        return JsonResponse({'context':context})
    
    
    
# 세션에 메모리 저장
def save_memory_to_session(request, memory):
    serialized_memory = serialize_memory(memory)
    request.session['memory'] = serialized_memory
# 메모리 직렬화
def serialize_memory(memory):
    if memory is None:
        return None
    
    chat_memory = serialize_chat_memory(memory.chat_memory) if hasattr(memory, 'chat_memory') else []
    input_key = memory.input_key if hasattr(memory, 'input_key') else "default_input_key"
    output_key = memory.output_key if hasattr(memory, 'output_key') else "default_output_key"
    return_messages = memory.return_messages if hasattr(memory, 'return_messages') else False
    memory_key = memory.memory_key if hasattr(memory, 'memory_key') else "default_memory_key"

    return json.dumps({
        'chat_memory': chat_memory,
        'input_key': input_key,
        'output_key': output_key,
        'return_messages': return_messages,
        'memory_key': memory_key
    })
# 채팅 메모리 직렬화
def serialize_chat_memory(chat_memory):
    serialized_chat_memory = []
    for message in chat_memory.messages:
        serialized_chat_memory.append(serialize_message(message))
    return serialized_chat_memory
# 메시지 객체를 직렬화
def serialize_message(message):
    return {
        'type': type(message).__name__,
        'content': message.content
    }
    
    
# 세션에서 메모리 로드
def load_memory_from_session(request):
    serialized_memory = request.session.get('memory')
    if serialized_memory:
        return deserialize_memory(serialized_memory)
    else:
        return None
# 메모리 역직렬화
def deserialize_memory(serialized_memory):
    if serialized_memory is None:
        return None
    
    memory_data = json.loads(serialized_memory)
    chat_memory = deserialize_chat_memory(memory_data['chat_memory']) if 'chat_memory' in memory_data else []
    input_key = memory_data['input_key'] if 'input_key' in memory_data else "default_input_key"
    output_key = memory_data['output_key'] if 'output_key' in memory_data else "default_output_key"
    return_messages = memory_data['return_messages'] if 'return_messages' in memory_data else False
    memory_key = memory_data['memory_key'] if 'memory_key' in memory_data else "default_memory_key"

    memory = ConversationBufferMemory(
        chat_memory=ChatMessageHistory(messages=chat_memory),
        input_key=input_key,
        output_key=output_key,
        return_messages=return_messages,
        memory_key=memory_key
    )

    return memory
# 채팅 메모리 역직렬화
def deserialize_chat_memory(serialized_chat_memory):
    deserialized_chat_memory = []
    for item in serialized_chat_memory:
        deserialized_chat_memory.append(deserialize_message(item))
    return deserialized_chat_memory
# 메시지 객체 역직렬화
def deserialize_message(data):
    if data['type'] == 'HumanMessage':
        return HumanMessage(content=data['content'])
    elif data['type'] == 'AIMessage':
        return AIMessage(content=data['content'])
    else:
        raise ValueError(f"Unknown message type: {data['type']}")
    
def history(request):
    username = ""
    if request.user.is_authenticated:
        username = request.user.username
    chats = Chats.objects.filter(username=username)
    return render(request, 'selfchatgpt/history.html', {'chats': chats})