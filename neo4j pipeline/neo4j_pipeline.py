import os
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
import re
import csv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


#Code Structure:
#Start Functions
#Host Functions
#Pathogen Functions
#Main

#Start
######################################################################################################

def welcome():
    print("Welcome to the Neo4j Pipeline (He Group)")

def menu_selection(debug_mode):
    user_choice = input("""
    Choose the following options: \n
        1 - Insert Data
        d - Debug Mode
        q - Quit\n
    """)
    if user_choice.lower() not in ['1', 'q', 'd']:
        print("\nERROR ~~~ INVALID CHOICE ~~~ ERROR\n")

    if user_choice == 'd':
        debug_mode = not debug_mode
        print(f"Debug Mode Set To: {debug_mode}")

    if user_choice == '1':
        insert_data_menu(debug_mode)

    if user_choice.lower() == 'q':
        return False, debug_mode
    return True, debug_mode

def connect_to_neo4j_DB():
    try:
        load_dotenv("neo4j_pipeline.env")
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        global driver
        driver = GraphDatabase.driver(uri, auth=(user, password))
        print("Connection Sucessful!!!")
    except:
        print("\nERROR ~~~ NEO4J CONNECTION FAILURE ~~~ ERROR\n")

def load_langchain_api():
    try:
        load_dotenv("langchain.env")
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_KEY")
        os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING")
        os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
        os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT")
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", )
        print("Loaded AI Environment Sucessfully\n")
        return chat_model
    except:
        print("\nERROR ~~~ AI ENVIRONMENT FILE FAILURE ~~~ ERROR\n")

def insert_data_menu(debug_mode):
    model = load_langchain_api()
    insert_data_menu_input = input("""
    Choose The Following Input Methods:\n
        1 - Insert Host Data
        2 - Insert Pathogen Data
        3 - Insert Vaccine Data
        t - Test
        q - Quit\n
    """)
    if insert_data_menu_input.lower() not in ['1','2','3','q', 't']:
        print("\nERROR ~~~ INVALID CHOICE ~~~ ERROR\n")
    if insert_data_menu_input.lower() == 'q':
        return False
    if insert_data_menu_input == '1':
        insert_host_data(debug_mode)
    if insert_data_menu_input == '2':
        insert_pathogen_data_menu(model, debug_mode)
    if insert_data_menu_input == '3':
        insert_pathogen_data_with_unstructured_host(model, debug_mode)
    if insert_data_menu_input.lower() == 't':
        unstructured_host_range = "Plague is primarily a zoonotic infection, occurring in urban or wild rodent populations.  Rodents that could be characterized as enzootic hosts (i.e., in what rodent populations Yersinia pestis is found naturally) have not been conclusively identified, but certain species of rat, vole, mouse, and gerbil are suspected [Ref49: Perry et al., 1997]."
        host_id_creation_for_unstructured_hosts(unstructured_host_range, model, debug_mode)
    
def insert_pathogen_data_menu(model, debug_mode):
    print("\nWelcome to Pathogen Insert Select an Option:\n")
    while True:
        user_input = input("""
        1 - Structured Insertion
        2 - Unstructured Insertion
        q - Quit\n""")

        if user_input.lower() not in ['1', '2', 'q']:
            print("\nERROR ~~~ INVALID CHOICE ~~~ ERROR\n")
            continue
        
        if user_input == '1':
            insert_pathogen_data_with_structured_host(debug_mode)
        if user_input == '2':
            insert_pathogen_data_with_unstructured_host(model, debug_mode)
        if user_input.lower() == 'q':
            break


#Host
######################################################################################################

def batch_insert_host(tx, host_batch_data):
        query = """
        UNWIND $host_batch_data AS host
        MERGE (hn: HostName {name: host.c_host_name})
        SET hn.HOST_ID = host.c_host_id
        SET hn.HOST_SCIENTIFIC_NAME = host.c_scientific_name
        SET hn.HOST_TAXONOMY_ID = host.c_host_taxonomy_id
        """
        tx.run(query, host_batch_data=host_batch_data)

def insert_host_data(debug_mode):
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
                    host_id = host_file_row["c_host_id"]
                    host_name = host_file_row["c_host_name"]
                    host_scientific_name = host_file_row["c_scientific_name"]
                    host_taxonomy_id = host_file_row["c_taxonomy_id"]
                    if debug_mode:
                        print(f"Host ID: {host_id}, Host Name: {host_name}, Host Scientific Name: {host_scientific_name}, Host Taxonomy ID: {host_taxonomy_id}")
                except:
                    print("\nERROR ~~~ Failed To Retrieve Data - Is Formatting Wrong? ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)
                    continue
                host_batch_data.append({
                    "c_host_id": host_id,
                    "c_host_name": host_name,
                    "c_scientific_name": host_scientific_name,
                    "c_host_taxonomy_id": host_taxonomy_id,
                })

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
    except:
        print("ERROR ~~~ INVALID FILE NAME ~~~ ERROR")


#Pathogen
######################################################################################################

def batch_insert_pathogen(tx, pathogen_batch_data):
    query = """
    UNWIND $pathogen_batch_data AS pathogen
    MERGE (pn: PathogenName {name: pathogen.c_pathogen_name})
    MERGE (pt: PathogenType {name: pathogen.c_organism_type})
    MERGE (dn: DiseaseName {name: pathogen.c_disease_name})
    
    MERGE (pn)-[:PATHOGEN_TYPE]->(pt)
    MERGE (pn)-[:TARGETS_DISEASE]->(dn)

    WITH pn, pathogen
    UNWIND pathogen.c_host_range as host_id
    MATCH (hn:HostName {HOST_ID: toString(host_id)})
    MERGE (pn)-[:TARGET_HOST]->(hn)

    SET pn.PATHOGEN_ID = pathogen.c_pathogen_id
    SET pn.PATHOGEN_TAXONOMY_ID = pathogen.c_taxonomy_id
    SET pn.PREPARATION_VO_ID = pathogen.c_preparation_vo_id
    SET pn.VACCINE_VO_ID = pathogen.c_vaccine_vo_id
    SET pn.PROTEIN_VO_ID = pathogen.c_protein_vo_id
    SET pn.PATHOGENESIS = pathogen.c_pathogenesis
    SET pn.PROTECTIVE_IMMUNITY = pathogen.c_protective_immunity
    SET pn.GRAM = pathogen.c_gram
    """
    tx.run(query, pathogen_batch_data=pathogen_batch_data)

def insert_pathogen_data_with_structured_host(debug_mode):
    pathogen_file_name_input = input("Enter the file name of the data in data folder: \n")
    pathogen_file_path = f"data\{pathogen_file_name_input}"
    error_count = 0
    error_lines = []
    try:
        with open(pathogen_file_path, "r", encoding="utf-8") as pathogen_file:
            print("File Opened!")
            pathogen_batch_data = []

            pathogen_start_time = time.time()

            pathogen_reader = csv.DictReader(pathogen_file)
            for index, pathogen_file_row in enumerate(pathogen_reader, start=1):
                try:
                    pathogen_id = pathogen_file_row["c_pathogen_id"]
                    pathogen_name = pathogen_file_row["c_pathogen_name"]
                    pathogen_taxonomy_id = pathogen_file_row["c_taxon_id"]
                    pathogen_disease_name = pathogen_file_row["c_disease_name"]
                    pathogen_host_range = pathogen_file_row["c_host_range"]
                    pathogen_organism_type = pathogen_file_row["c_organism_type"].split(',') if pathogen_file_row["c_host_range"] else []
                    pathogen_preparation_vo_id = pathogen_file_row["c_preparation_vo_id"]
                    pathogen_vaccine_vo_id = pathogen_file_row["c_vaccine_vo_id"]
                    pathogen_protein_vo_id = pathogen_file_row["c_protein_vo_id"]
                    pathogen_pathogenesis = pathogen_file_row["c_pathogenesis"]
                    pathogen_protective_immunity = pathogen_file_row["c_protective_immunity"]
                    pathogen_gram = pathogen_file_row["c_gram"]

                    pathogen_batch_data.append({
                        "c_pathogen_id": pathogen_id,
                        "c_pathogen_name": pathogen_name,
                        "c_taxonomy_id": pathogen_taxonomy_id,
                        "c_organism_type": pathogen_organism_type,
                        "c_disease_name": pathogen_disease_name,
                        "c_host_range": pathogen_host_range,
                        "c_preparation_vo_id": pathogen_preparation_vo_id,
                        "c_vaccine_vo_id": pathogen_vaccine_vo_id,
                        "c_protein_vo_id": pathogen_protein_vo_id,
                        "c_pathogenesis": pathogen_pathogenesis,
                        "c_protective_immunity": pathogen_protective_immunity,
                        "c_gram": pathogen_gram,
                    })
                    if debug_mode:
                        print(f"""{pathogen_name} with ID: {pathogen_id} and taxon ID: {pathogen_taxonomy_id}\n
                        Causes disease: {pathogen_disease_name} in {pathogen_host_range}\n
                        Is type: {pathogen_organism_type}, preparation VO ID: {pathogen_preparation_vo_id}, vaccine VO ID: {pathogen_vaccine_vo_id}, protein VO ID: {pathogen_protein_vo_id}\n
                        Pathogenesis: {pathogen_pathogenesis}\n
                        Pathogen Protective Immunity: {pathogen_protective_immunity}\n
                        Pathogen Gram: {pathogen_gram}
                        """)
                except:
                    print("\nERROR ~~~ Failed to Retrieve Data - Is Formatting Wrong? ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)

                if len(pathogen_batch_data) >= 10:
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
            print(f"""Inserted {index-error_count} Lines Sucessfully In {pathogen_time_end-pathogen_start_time}\n
            Had {error_count} Errors, Sucess Rate = {(index-error_count)/index * 100}%\n
            Lines That Failed Insertion: {error_lines}""")
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")


def host_id_creation_for_unstructured_hosts(unstructured_host_range, model, debug_mode):
    restructured_query_template = ChatPromptTemplate([
    ("system", """
    You are a helpful assistant that turns unstructured ranges of hosts and output the respective ids. Return a list of numbers. If you are unsure only put 0.
    2 - Human
    3 - Mouse
    4 - Rat
    5 - Monkey
    6 - Rabbit
    7 - Guinea Pig
    8 - Chicken
    9 - Ducks
    12 - Cattle
    13 - Goat
    15 - Pig
    16 - Hamster
    17 - Sheep
    18 - Horse
    19 - Ferret
    24 - Copper Pheasant
    26 - chincillas
    27 - Water buffalo
    28 - Squirrel
    29 - Deer
    30 - Buffalo
    31 - Bear
    32 - Deer mouse
    33 - Vole
    34 - Raven
    35 - Brown Trout
    36 - Dog
    37 - Cat
    38 - Turkey
    39 - Macaque
    40 - Mogolian Gerbil
    41 - Gerbil
    42 - Chimpanzee
    43 - Bank vole
    44 - Tree shrew
    45 - Rainbow trout 
    59 - None
    47 - Gray wolf
    48 - Fish
    49 - Trouts, salmons & chars
    50 - Parrot
    51 - Birds
    52 - Catfishes
    53 - Carnivores
    54 - sei whale
    55 - Baboon

    EXAMPLES:
    1. user query: "Host ranges include the following:  livestock or other herbivores (eg, cattle, sheep, goats, pigs, bison, water buffalo) acquire infection by 
    consuming contaminated soil or feed; spores are infectious agents that can enter the human body through skin lesions, ingestion, or inhalation; and laboratory 
    animal models include Guinea pigs, Syrian hamsters, and various mouse models [Ref115:PathPort]."
    output: 12, 17, 13, 15, 27, 2, 16, 3
    2. user query: "Cattle"
    output: 12
    3. user query: "Plague is primarily a zoonotic infection, occurring in urban or wild rodent populations.  Rodents that could be characterized as enzootic hosts 
     (i.e., in what rodent populations Yersinia pestis is found naturally) have not been conclusively identified, but certain species of rat, vole, mouse, and gerbil 
     are suspected [Ref49: Perry et al., 1997]."
    output: 4, 33, 3, 41, 40
    """),
    ("human", "The host range to convert into integer is: {host_range}")])
    llm_chain = restructured_query_template | model
    list_output = llm_chain.invoke({"host_range": unstructured_host_range})
    if debug_mode:
        print(list_output.content)
        print(list_output.content.split(', '))
    return list(map(int, list_output.content.split(', ')))

def insert_pathogen_data_with_unstructured_host(model, debug_mode): 
    pathogen_file_name_input = input("Enter the file name of the data in data folder: \n")
    pathogen_file_path = f"data\{pathogen_file_name_input}"
    error_count = 0
    error_lines = []
    try:
        with open(pathogen_file_path, "r", encoding="utf-8") as pathogen_file:
            print("File Opened!")
            pathogen_batch_data = []

            pathogen_start_time = time.time()

            pathogen_reader = csv.DictReader(pathogen_file)
            for index, pathogen_file_row in enumerate(pathogen_reader, start=1):
                try:
                    pathogen_id = pathogen_file_row["c_pathogen_id"]
                    pathogen_name = pathogen_file_row["c_pathogen_name"]
                    pathogen_taxonomy_id = pathogen_file_row["c_taxon_id"]
                    pathogen_disease_name = pathogen_file_row["c_disease_name"]
                    pathogen_host_range = pathogen_file_row["c_host_range"]
                    pathogen_organism_type = pathogen_file_row["c_organism_type"].split(',') if pathogen_file_row["c_host_range"] else []
                    pathogen_preparation_vo_id = pathogen_file_row["c_preparation_vo_id"]
                    pathogen_vaccine_vo_id = pathogen_file_row["c_vaccine_vo_id"]
                    pathogen_protein_vo_id = pathogen_file_row["c_protein_vo_id"]
                    pathogen_pathogenesis = pathogen_file_row["c_pathogenesis"]
                    pathogen_protective_immunity = pathogen_file_row["c_protective_immunity"]
                    pathogen_gram = pathogen_file_row["c_gram"]

                    
                    generated_host_range = host_id_creation_for_unstructured_hosts(unstructured_host_range=pathogen_host_range, model=model, debug_mode=debug_mode)

                    if debug_mode:
                        print(f"Generated Host Range Prior to Insertion: {generated_host_range}")

                    pathogen_batch_data.append({
                        "c_pathogen_id": pathogen_id,
                        "c_pathogen_name": pathogen_name,
                        "c_taxonomy_id": pathogen_taxonomy_id,
                        "c_organism_type": pathogen_organism_type,
                        "c_disease_name": pathogen_disease_name,
                        "c_host_range": generated_host_range,
                        "c_preparation_vo_id": pathogen_preparation_vo_id,
                        "c_vaccine_vo_id": pathogen_vaccine_vo_id,
                        "c_protein_vo_id": pathogen_protein_vo_id,
                        "c_pathogenesis": pathogen_pathogenesis,
                        "c_protective_immunity": pathogen_protective_immunity,
                        "c_gram": pathogen_gram,
                    })
                    if debug_mode:
                        print(f"""{pathogen_name} with ID: {pathogen_id} and taxon ID: {pathogen_taxonomy_id}\n
                        Causes disease: {pathogen_disease_name} in {pathogen_host_range}\n
                        Is type: {pathogen_organism_type}, preparation VO ID: {pathogen_preparation_vo_id}, vaccine VO ID: {pathogen_vaccine_vo_id}, protein VO ID: {pathogen_protein_vo_id}\n
                        Pathogenesis: {pathogen_pathogenesis}\n
                        Pathogen Protective Immunity: {pathogen_protective_immunity}\n
                        Pathogen Gram: {pathogen_gram}
                        """)
                except:
                    print("\nERROR ~~~ Failed to Retrieve Data - Is Formatting Wrong? ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)

                if len(pathogen_batch_data) >= 10:
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
            print(f"""Inserted {index-error_count} Lines Sucessfully In {pathogen_time_end-pathogen_start_time}\n
            Had {error_count} Errors, Sucess Rate = {(index-error_count)/index * 100}%\n
            Lines That Failed Insertion: {error_lines}""")
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")


#Vaccine
######################################################################################################

#create nodes for 
# - delivery method (route) (multiple)
# - Manufacturer (multiple)
# - licence 
# - vaccine type
# - location licsneed (multiple)

#create properties for

# - vaccine name
# - proper name
# - brand name
# - vaccine id
# - vo id
# - Description
# - Full text
# - model_host
# - c_host_specieis_2
# - preparation
# - prepartion_vo_id
# - is combination vaccine (Yes, No)
# - Adjuvant
# - Storange
# - Virulence
# - Antigen
# - Allegrn
# - preservetaive
# - contraindication
# - usage_age
# - vector
# - curation flag
# - c_cvx_code
# - c_cvx_desc


#create connections to
# - pathogen (pathogen_id)
# - host speciesi (host_spciies_id)

#Main
######################################################################################################

#Questions
#Would like to link pathogen and hosts but hosts in pathogen.csv is unstructured. Could use structured prompting with LLM
#What is host id = 0
#Do we want a chat functionality
def main():
    debug_mode = False
    welcome()
    connect_to_neo4j_DB()
    while True:
        menu_choice, debug_mode = menu_selection(debug_mode)
        if menu_choice == False:
            break

if __name__ == "__main__":
    main()