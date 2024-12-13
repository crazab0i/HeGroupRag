import os
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
import re
import csv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


#Structure:
#Startup
#Insert
    #-Host
    #-Pathogen
    #-Vaccine
#VaxGPT
#Main

#Startup
########################################################################################################################
def welcome():
    print("Welcome to VaxNeo4j")

def connect_to_neo4j_DB():
    try:
        load_dotenv("neo4j_pipeline.env")
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        global driver
        driver = GraphDatabase.driver(uri, auth=(user, password))
        print("Neo4j Connection Sucessful")
    except:
        print("\nERROR ~~~ NEO4J CONNECTION FAILURE ~~~ ERROR\n")

def load_langchain_api():
    try:
        load_dotenv("langchain.env")
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")
        os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING")
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
        global chat_model
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", )
        print("Loaded AI Environment Sucessfully\n")
    except:
        print("\nERROR ~~~ AI ENVIRONMENT FILE FAILURE ~~~ ERROR\n")

def main_menu():
    main_menu_user_input = input("""Please Select an Option:
    1 - Insert Data
    2 - VaxGPT
    d - Debug Mode
    q - Quit\n """)
    if main_menu_user_input not in ['1', '2', 'd', 'q']:
        print("\nERROR ~~~ Invalid User Input ~~~ ERROR\n")
    match main_menu_user_input:
        case '1':
            insert_menu()
        case '2':
            VaxGPT()
        case 'q':
            return False
        case 'd':
            global debug_mode
            debug_mode = not debug_mode
            print(f"Debug mode set to: {debug_mode}")
#Insert
########################################################################################################################

def insert_menu():
    insert_menu_user_input = input("""Please Select an Option
    1 - Insert Host Data
    2 - Insert Pathogen Data
    3 - Insert Vaccine Data\n""")
    if insert_menu_user_input not in ['1','2','3']:
        print("\nERROR ~~~ Invalid User Input ~~~ ERROR\n")
    match insert_menu_user_input:
        case '1':
            insert_host_data()
        case '2':
            insert_pathogen_data()
        case '3':
            insert_vaccine_data()

def batch_insert_host(tx, host_batch_data):
        query = """
        UNWIND $host_batch_data AS host
        MERGE (hn: HostName {name: host.c_host_name})
        SET hn.HOST_ID = host.c_host_id
        SET hn.HOST_SCIENTIFIC_NAME = host.c_scientific_name
        SET hn.HOST_TAXONOMY_ID = host.c_host_taxonomy_id
        """
        tx.run(query, host_batch_data=host_batch_data)

def insert_host_data():
    host_file_name_input = input("Enter the file name of the data in data folder: \n")
    host_file_path = f"data\{host_file_name_input}"
    error_count = 0
    error_lines = []
    try:
        with open(host_file_path, "r", encoding="utf-8") as host_file:
            print("File Opened!")
            host_batch_data = []
            
            host_time_start = time.time()

            host_reader = csv.DictReader(host_file)
            for index, host_file_row in enumerate(host_reader,start=1):
                try:
                    host_batch_data.append({
                    "c_host_id": host_file_row["c_host_id"],
                    "c_host_name": host_file_row["c_host_name"],
                    "c_scientific_name": host_file_row["c_scientific_name"],
                    "c_host_taxonomy_id": host_file_row["c_taxonomy_id"],
                })
                    
                    if debug_mode:
                        print(f"Host ID: {host_file_row['c_host_id']}, Host Name: {host_file_row['c_host_name']}, Host Scientific Name: {host_file_row['c_scientific_name']}, Host Taxonomy ID: {host_file_row['c_taxonomy_id']}")
                except Exception as e:
                    print(f"\nERROR ~~~ {e} ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)
                    continue

                if len(host_batch_data) >= 10:
                    with driver.session() as session:
                        session.execute_write(batch_insert_host, host_batch_data)
                        host_batch_data.clear()
                        print(f"Inserted The Batch, Current Count Inserted: {index-error_count}")
            if host_batch_data:
                with driver.session() as session:
                    session.execute_write(batch_insert_host, host_batch_data)
                    host_batch_data.clear()
                    print(f"Inserted Last Batch!!!")

        host_time_end = time.time()
        print(f"""Inserted {index-error_count} Lines Sucessfully In {host_time_end-host_time_start}\n
        Had {error_count} Errors, Sucess Rate = {(index-error_count)/index * 100}%\n
        Lines That Failed Insertion: {error_lines}""")
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")

def batch_insert_pathogen(tx, pathogen_batch_data):
        query = """
        UNWIND $pathogen_batch_data AS pathogen
        MERGE (pn: PathogenName {name: pathogen.c_pathogen_name})
        SET pn.PATHOGEN_ID = pathogen.c_pathogen_id,
            pn.TAXON_ID = pathogen.c_taxon_id,
            pn.DISEASE_NAME = pathogen.c_disease_name,
            pn.HOST_RANGE = pathogen.c_host_range,
            pn.ORGANISM_TYPE = pathogen.c_organism_type,
            pn.PREPERATION_VO_ID = pathogen.c_preparation_vo_id,
            pn.VACCINE_VO_ID = pathogen.c_vaccine_vo_id,
            pn.PROTEIN_VO_ID = pathogen.c_protein_vo_id,
            pn.PATHOGENESIS = pathogen.c_pathogenesis,
            pn.PROTECTIVE_IMMNUITY = pathogen.c_protective_immunity,
            pn.GRAM = pathogen.c_gram

        """
        tx.run(query, pathogen_batch_data=pathogen_batch_data)

def insert_pathogen_data():
    pathogen_file_name_input = input("Enter the file name of the data in data folder: \n")
    pathogen_file_path = f"data\{pathogen_file_name_input}"
    error_count = 0
    error_lines = []
    try:
        with open(pathogen_file_path, "r", encoding="utf-8") as pathogen_file:
            print("File Opened!")
            pathogen_batch_data = []
            
            pathogen_time_start = time.time()

            pathogen_reader = csv.DictReader(pathogen_file)
            for index, pathogen_file_row in enumerate(pathogen_reader,start=1):
                try:
                    pathogen_batch_data.append({
                    "c_pathogen_id": pathogen_file_row["c_pathogen_id"],
                    "c_pathogen_name": pathogen_file_row["c_pathogen_name"],
                    "c_taxon_id": pathogen_file_row["c_taxon_id"],
                    "c_disease_name": pathogen_file_row["c_disease_name"],
                    "c_host_range": pathogen_file_row["c_host_range"],
                    "c_organism_type": pathogen_file_row["c_organism_type"],
                    "c_preparation_vo_id": pathogen_file_row["c_preparation_vo_id"],
                    "c_vaccine_vo_id": pathogen_file_row["c_vaccine_vo_id"],
                    "c_protein_vo_id": pathogen_file_row["c_protein_vo_id"],
                    "c_pathogenesis": pathogen_file_row["c_pathogenesis"],
                    "c_protective_immunity": pathogen_file_row["c_protective_immunity"],
                    "c_gram": pathogen_file_row["c_gram"],
                })
                    
                    if debug_mode:
                        print(f"Pathogen ID: {pathogen_file_row['c_pathogen_id']}, Pathogen Name: {pathogen_file_row['c_pathogen_name']}, Pathogen Pathogenesis: {pathogen_file_row['c_pathogenesis']}, Pathogen Taxonomy ID: {pathogen_file_row['c_taxon_id']}")
                except Exception as e:
                    print(f"\nERROR ~~~ {e} ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)
                    continue

                if len(pathogen_batch_data) >= 50:
                    with driver.session() as session:
                        session.execute_write(batch_insert_pathogen, pathogen_batch_data)
                        pathogen_batch_data.clear()
                        print(f"Inserted The Batch, Current Count Inserted: {index-error_count}")
            if pathogen_batch_data:
                with driver.session() as session:
                    session.execute_write(batch_insert_pathogen, pathogen_batch_data)
                    pathogen_batch_data.clear()
                    print(f"Inserted Last Batch!!!")

        pathogen_time_end = time.time()
        print(f"""Inserted {index-error_count} Lines Sucessfully In {pathogen_time_end-pathogen_time_start}\n
        Had {error_count} Errors, Sucess Rate = {(index-error_count)/index * 100}%\n
        Lines That Failed Insertion: {error_lines}""")
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")


def batch_insert_vaccine(tx, vaccine_batch_data):
        query = """
        UNWIND $vaccine_batch_data AS vaccine
        MERGE (vn: VaccineName {name: vaccine.c_vaccine_name})
        SET vn.VACCINE_ID = vaccine.c_vaccine_id,
            vn.VACCINE_TYPE = vaccine.c_type,
            vn.IS_COMBINATION_VACCINE = vaccine.c_is_combination_vaccine,
            vn.DESCRIPTION = vaccine.c_description,
            vn.ADJUVANT = vaccine.c_adjuvant,
            vn.STORAGE = vaccine.c_storage,
            vn.VIRULENCE = vaccine.c_virulence,
            vn.PREPARATION = vaccine.c_preparation,
            vn.BRAND_NAME = vaccine.c_brand_name,
            vn.FULL_TEXT = vaccine.c_full_text,
            vn.ANTIGEN = vaccine.c_antigen,
            vn.CURATION_FLAG = vaccine.c_curation_flag,
            vn.VECTOR = vaccine.c_vector,
            vn.PROPER_NAME = vaccine.c_proper_name,
            vn.MANUFACTURER = vaccine.c_manufacturer,
            vn.CONTRAINDICATION = vaccine.c_contraindication,
            vn.STATUS = vaccine.c_status,
            vn.LOCATION_LICENSED = vaccine.c_location_licensed,
            vn.ROUTE = vaccine.c_route,
            vn.VO_ID = vaccine.c_vo_id,
            vn.USAGE_AGE = vaccine.c_usage_age,
            vn.MODEL_HOST = vaccine.c_model_host,
            vn.PRESERVATIVE = vaccine.c_preservative,
            vn.ALLERGEN = vaccine.c_allergen,
            vn.PREPARATION_VO_ID = vaccine.c_preparation_vo_id,
            vn.HOST_SPECIES2 = vaccine.c_host_species2,
            vn.CVX_CODE = vaccine.c_cvx_code,
            vn.CVX_DESC = vaccine.c_cvx_desc

        WITH vn, vaccine
        MATCH (pn: PathogenName {PATHOGEN_ID: vaccine.c_pathogen_id})
        MERGE (vn)-[:TARGETS_PATHOGEN]->(pn)
        WITH vn, vaccine
        MATCH (hn: HostName {HOST_ID: vaccine.c_host_species})
        MERGE (vn)-[:TARGETS_HOST]->(hn)
"""
        tx.run(query, vaccine_batch_data=vaccine_batch_data)

def insert_vaccine_data():
    vaccine_file_name_input = input("Enter the file name of the data in data folder: \n")
    vaccine_file_path = f"data\{vaccine_file_name_input}"
    error_count = 0
    error_lines = []
    try:
        with open(vaccine_file_path, "r", encoding="utf-8") as vaccine_file:
            print("File Opened!")
            vaccine_batch_data = []
            
            vaccine_time_start = time.time()

            vaccine_reader = csv.DictReader(vaccine_file)
            for index, vaccine_file_row in enumerate(vaccine_reader,start=1):
                try:
                    vaccine_batch_data.append({
                    "c_vaccine_id": vaccine_file_row["c_vaccine_id"],
                    "c_vaccine_name": vaccine_file_row["c_vaccine_name"],
                    "c_type": vaccine_file_row["c_type"],
                    "c_is_combination_vaccine": vaccine_file_row["c_is_combination_vaccine"],
                    "c_description": vaccine_file_row["c_description"],
                    "c_adjuvant": vaccine_file_row["c_adjuvant"],
                    "c_storage": vaccine_file_row["c_storage"],
                    "c_pathogen_id": vaccine_file_row["c_pathogen_id"],
                    "c_virulence": vaccine_file_row["c_virulence"],
                    "c_preparation": vaccine_file_row["c_preparation"],
                    "c_brand_name": vaccine_file_row["c_brand_name"],
                    "c_full_text": vaccine_file_row["c_full_text"],
                    "c_antigen": vaccine_file_row["c_antigen"],
                    "c_curation_flag": vaccine_file_row["c_curation_flag"],
                    "c_vector": vaccine_file_row["c_vector"],
                    "c_proper_name": vaccine_file_row["c_proper_name"],
                    "c_manufacturer": vaccine_file_row["c_manufacturer"],
                    "c_contraindication": vaccine_file_row["c_contraindication"],
                    "c_status": vaccine_file_row["c_status"],
                    "c_location_licensed": vaccine_file_row["c_location_licensed"],
                    "c_host_species": vaccine_file_row["c_host_species"],
                    "c_route": vaccine_file_row["c_route"],
                    "c_vo_id": vaccine_file_row["c_vo_id"],
                    "c_usage_age": vaccine_file_row["c_usage_age"],
                    "c_model_host": vaccine_file_row["c_model_host"],
                    "c_preservative": vaccine_file_row["c_preservative"],
                    "c_allergen": vaccine_file_row["c_allergen"],
                    "c_preparation_vo_id": vaccine_file_row["c_preparation_vo_id"],
                    "c_host_species2": vaccine_file_row["c_host_species2"],
                    "c_cvx_code": vaccine_file_row["c_cvx_code"],
                    "c_cvx_desc": vaccine_file_row["c_cvx_desc"],
                    })
                    
                    if debug_mode:
                        print(f"Pathogen ID: {vaccine_file_row['c_vaccine_id']}, Vaccine Name: {vaccine_file_row['c_vaccine_name']}, Vaccine Type: {vaccine_file_row['c_type']}, Pathogen ID: {vaccine_file_row['c_pathogen_id']}")
                except Exception as e:
                    print(f"\nERROR ~~~ {e} ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)
                    continue

                if len(vaccine_batch_data) >= 50:
                    with driver.session() as session:
                        session.execute_write(batch_insert_vaccine, vaccine_batch_data)
                        vaccine_batch_data.clear()
                        print(f"Inserted The Batch, Current Count Inserted: {index-error_count}")
            if vaccine_batch_data:
                with driver.session() as session:
                    session.execute_write(batch_insert_vaccine, vaccine_batch_data)
                    vaccine_batch_data.clear()
                    print(f"Inserted Last Batch!!!")

        vaccine_time_end = time.time()
        print(f"""Inserted {index-error_count} Lines Sucessfully In {vaccine_time_end-vaccine_time_start}\n
        Had {error_count} Errors, Sucess Rate = {(index-error_count)/index * 100}%\n
        Lines That Failed Insertion: {error_lines}""")
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")

#edge case in vaccine insertion where same name vaccines override each other and merge. They miss properties and have weird functionaliy when it comes to relationships. 
# SARS-CoV VLP-MHV vaccine, VRP-SARS-N vaccine, MVvac2-CoV-solS
#merge vo_id or vaccine_vo_id (vaccine_name)
#vaccine data getting cleaned
#

#Startup
########################################################################################################################

def VaxGPT():
    print("Welcome to VaxGPT")
    user_query_input = input("Enter A Query About Vaccines in the He Group Neo4j Database\n")
    converted_cypher_query = user_query_to_cypher(user_query_input)
    if debug_mode:
        print(f"Resultant Cypher Query: {converted_cypher_query}")
    final_answer = context_generating_answer(converted_cypher_query, user_query_input)
    print(f"\n{final_answer}\n")

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
    if debug_mode:
        print(f"Retrieved Data Results: {results}")
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


#Main
########################################################################################################################

def main():
    global debug_mode
    debug_mode = False
    welcome()
    connect_to_neo4j_DB()
    load_langchain_api()
    while True:
        menu_quit = main_menu()
        if menu_quit == False:
            break

if __name__ == "__main__":
    main()


#notes
#add memory and more chat functionality
#front-end???
#merge vo_id or vaccine_vo_id