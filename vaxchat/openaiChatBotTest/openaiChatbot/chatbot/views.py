from django.shortcuts import render, redirect
from django.http import JsonResponse
import os
from dotenv import load_dotenv
from openai import OpenAI
from django.contrib import auth
from django.contrib.auth.models import User
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from neo4j import GraphDatabase
import re
from .models import Chat
from django.utils import timezone

load_dotenv("openai.env")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")
load_dotenv("langchain.env")
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
chat_model = ChatOpenAI(model="gpt-3.5-turbo")
load_dotenv("neo4j_pipeline.env")
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")
global driver
driver = GraphDatabase.driver(uri, auth=(user, password))


def determine_if_vaccine_related(user_query):
    query = ChatPromptTemplate([
        ("system", """
         You are a helpful assistant, can you determine if this user query is related to vaccines or something similar. If that query is quite apart from anything regarding vaccines,
         return false. If the vaccine is related to vaccines return true. If you are unsure return true.
         """,
         ),
         ("human", "The user query is: {user_query}")
    ])
    llm_decision_chain = query | chat_model
    decision_boolean = llm_decision_chain.invoke({"user_query": user_query})
    return decision_boolean.content

def user_query_to_cypher(user_query):
    restructured_cypher_query = ChatPromptTemplate([
        ("system", """
        You are a helpful assistant that rewrites natural language user queries into Cypher queries for a Neo4j vaccine database. Include nodes,
         relationships, and relevant properties in the queries. Use a default limit of 5 if the user doesn't specify. Keep in mind that all properties
         and names of nodes are strings including numbers such as HOST_ID. It is avisible to create robust and flexible queries when matching strings,
         use CONTAIN and REGEX to ensure a match is found, also consider case insensitivity. Your response should only include the cypher query itself.
        Node Types and Properties:
         HostName (name, HOST_ID, HOST_SCIENTIFIC_NAME, HOST_TAXONOMY_ID)
         PathogenName (name, PATHOGEN_ID, TAXON_ID, DISEASE_NAME, HOST_RANGE, ORGANISM_TYPE, PREPARATION_VO_ID, VACCINE_VO_ID, PROTEIN_VO_ID, PATHOGENESIS, 
         PROTECTIVE_IMMUNITY, GRAM)
         VaccineName (name, VACCINE_ID, IS_COMBINATION_VACCINE, DESCRIPTION, ADJUVANT, STORAGE, VIRULENCE, PREPARATION, BRAND_NAME, FULL_TEXT, ANTIGEN, CURATION_FLAG,
         VECTOR, PROPER_NAME, MANUFACTURER, CONTRAINDICATION, STATUS, LOCATION_LICENSED, ROUTE, VO_ID, USAGE_AGE, MODEL_HOST, PRESERVATIVE, ALLERGEN, PREPARATION_VO_ID,
         HOST_SPECIES2, CVX_CODE, CVX_DESC)
        
        Relationships:
         (vn:VaccineName)-[:TARGETS_PATHOGEN]->(pn:PathogenName)
         (vn:VaccineName)-[:TARGETS_HOST]->(hn:HostName)

        Examples:
        1. user query: "Find vaccines targetting pathogens that cause disease in humans."
         cypher query output:
         MATCH (v:VaccineName)-[:TARGETS_PATHOGEN]->(p:PathogenName)
         MATCH (h:HostName {{name: "Human"}})
         WHERE p.DISEASE_NAME IS NOT NULL
         RETURN v.name AS Vaccine, p.name AS Pathogen, p.DISEASE_NAME AS DISEASE
         LIMIT 5
        2. user query: "What vaccines were made by Pfizer Inc.?"
         cypher query output:
         MATCH (v:VaccineName) 
         WHERE v.MANUFACTURER 
         CONTAINS "Pfizer Inc" 
         RETURN v.name 
         LIMIT 5
        3. user query: "What are the mosts common routes for brucella vaccines?"
         cypher query output: " 
         MATCH (v:VaccineName)-[:TARGETS_PATHOGEN]->(p:PathogenName)
        WHERE p.name CONTAINS "Brucella" AND v.ROUTE IS NOT NULL AND v.ROUTE <> "NA"
        RETURN v.ROUTE AS Route, COUNT(v.ROUTE) AS RouteCount
        ORDER BY RouteCount DESC
        LIMIT 5"
         """),
         ("human", "The user query to convert is: {user_query}")])
    llm_chain = restructured_cypher_query | chat_model
    converted_cypher_query = llm_chain.invoke({"user_query": user_query})
    cleaned_query = re.sub(r'```(?:cypher)?\n(.*?)\n```', r'\1', converted_cypher_query.content, flags=re.DOTALL)
    return cleaned_query


def context_generating_answer(cypher_query, user_query):
    try: 
        with driver.session() as session:
            retrieved_data = session.run(cypher_query)
            results = retrieved_data.data()
            if results is None:
                print("No Results Found.")
    except Exception as e:
        print(f"\nERROR ~~~ {e} ~~~ ERROR\n")
    final_structured_output = ChatPromptTemplate([
        ("system", """
        You are a helpful assistant that answers user queries with retrieved data from a vaccine graph database Answer the question to the best
         of your ability. If you lack confidence in your answer, indicate that the data retrieved may not be relevant to the user query.
        """),
        ("human", "The user query is {user_query} and the retrieved data: {retrieved_data}")
    ])
    try:
        llm_chain = final_structured_output | chat_model
        final_output = llm_chain.invoke({"user_query": user_query, "retrieved_data": results})
        return final_output.content
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")

def generic_response(user_query):
    basic_output = ChatPromptTemplate([
        ("system", """
    You are a helpful chat assistant that is part of a vaccine program. You are given non-related vaccine questions. To the best of your ability answer user questions
        """),
        ("human", "The user query is {user_query}")
    ])
    generic_llm_chain = basic_output | chat_model
    generic_response_output = generic_llm_chain.invoke({"user_query": user_query})
    return generic_response_output.content

def ask_openai(message):
    decision_boolean = determine_if_vaccine_related(message)
    if decision_boolean == "true":
        cypher_query = user_query_to_cypher(message)
        final_answer = context_generating_answer(cypher_query, message)
    else:
        final_answer = generic_response(message)
    return final_answer

def chatbot(request): 
    chats = Chat.objects.filter(user=request.user)
    if request.method == 'POST':
        message = request.POST.get('message')
        response = ask_openai(message)
        chat = Chat(user=request.user, message=message, response=response, created_at=timezone.now())
        chat.save()
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html', {'chats': chats})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('chatbot')
        else:
            error_message = "Invalid Username or Password"
            return render(request, 'login.html', {'error_message': error_message})
    else:
        return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            try:
                user = User.objects.create_user(username, email, password1)
                user.save()
                auth.login(request, user)
                return redirect('chatbot')
            except:
                error_message = "Error Creating Account"
                return render(request, 'register.html', {'error_message': error_message})
        else:
            error_message = "Passwords Don't Match"
            return render(request, 'register.html', {'error_message': error_message})
    return render(request, 'register.html')

def logout(request):
    auth.logout(request)
    return redirect('login')