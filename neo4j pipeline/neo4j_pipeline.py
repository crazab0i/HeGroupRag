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
        2 - VaxGPT
        d - Debug Mode
        q - Quit\n
    """)
    model = load_langchain_api()
    if user_choice.lower() not in ['1', '2', 'q', 'd']:
        print("\nERROR ~~~ INVALID CHOICE ~~~ ERROR\n")

    if user_choice == 'd':
        debug_mode = not debug_mode
        print(f"Debug Mode Set To: {debug_mode}")

    if user_choice == '1':
        insert_data_menu(model, debug_mode)

    if user_choice == '2':
        VaxGPT(model, debug_mode)

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

def insert_data_menu(model, debug_mode):
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
        insert_vaccine_data(model, debug_mode)
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
    SET pn.PATHOGEN_ID = pathogen.c_pathogen_id,
        pn.PATHOGEN_TAXONOMY_ID = pathogen.c_taxonomy_id,
        pn.PREPARATION_VO_ID = pathogen.c_preparation_vo_id,
        pn.VACCINE_VO_ID = pathogen.c_vaccine_vo_id,
        pn.PROTEIN_VO_ID = pathogen.c_protein_vo_id,
        pn.PATHOGENESIS = pathogen.c_pathogenesis,
        pn.PROTECTIVE_IMMUNITY = pathogen.c_protective_immunity,
        pn.GRAM = pathogen.c_gram
        
    MERGE (pt: PathogenType {name: pathogen.c_organism_type})
    MERGE (dn: DiseaseName {name: pathogen.c_disease_name})
    
    MERGE (pn)-[:PATHOGEN_TYPE]->(pt)
    MERGE (pn)-[:TARGETS_DISEASE]->(dn)

    WITH pn, pathogen
    UNWIND pathogen.c_host_range AS host_id
    MATCH (hn:HostName {HOST_ID: toString(host_id)})
    MERGE (pn)-[:TARGET_HOST]->(hn)


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
                    pathogen_organism_type = pathogen_file_row["c_organism_type"]
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
    You are a helpful assistant that turns unstructured ranges of hosts and output the respective ids. Return a list of numbers. If you are unsure or field is empty only put 0.
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
                    pathogen_organism_type = pathogen_file_row["c_organism_type"]
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

def batch_insert_vaccine(tx, vaccine_batch_data):
    query = """
    UNWIND $vaccine_batch_data AS vaccine
    MERGE (vn: VaccineName {name: vaccine.c_vaccine_name})
    MERGE (vt: VaccineType {name: vaccine.c_type})
    MERGE (vs: VaccineStatus {name: vaccine.c_status})

    MERGE (vn)-[:VACCINE_TYPE]->(vt)
    MERGE (vn)-[:VACCINE_STATUS]->(vs)

    WITH vn, vaccine
    UNWIND vaccine.c_location_licensed AS country
    MERGE (cl: VaccineCountryLicensed {name: country})
    MERGE (vn)-[:LICENSED_IN_COUNTRY]->(cl)

    WITH vn, vaccine
    UNWIND vaccine.c_manufacturer AS manufacturer
    MERGE (m: VaccineManufacturer {name: manufacturer})
    MERGE (vn)-[:MANUFACTURED_BY]->(m)
    
    WITH vn, vaccine
    UNWIND vaccine.c_route AS route
    MERGE (dm: VaccineDeliveryMethod {name: route})
    MERGE (vn)-[:HAS_DELIVERY_METHOD]->(dm)

    WITH vn, vaccine
    MATCH (pn:PathogenName {PATHOGEN_ID: vaccine.c_pathogen_id})
    MERGE (vn)-[:TARGETS_PATHOGEN]->(pn)

    WITH vn, vaccine
    MATCH (hn: HostName {HOST_ID: toString(vaccine.c_host_species)})
    MERGE (vn)-[:IN_HOST]->(hn)

    WITH vn, vaccine
    UNWIND vaccine.c_model_host as model_host_id
    MATCH (mh: HostName {HOST_ID: toString(model_host_id)})
    MERGE (vn)-[:MODEL_HOST]-(mh)

    WITH vn, vaccine
    SET vn.PROPER_NAME = vaccine.c_proper_name
    SET vn.BRAND_NAME = vaccine.c_brand_name
    SET vn.VACCINE_ID = vaccine.c_vaccine_id
    SET vn.VO_ID = vaccine.c_vo_id
    SET vn.DESCRIPTION = vaccine.c_description
    SET vn.FULL_TEXT = vaccine.c_full_text
    SET vn.HOST_SPECIES2 = vaccine.c_host_species2
    SET vn.PREPARATION = vaccine.c_preparation
    SET vn.PREPARATION_VO_ID = vaccine.c_preparation_vo_id
    SET vn.IS_COMBINATION_VACCINE = vaccine.c_is_combination_vaccine
    SET vn.ADJUVANT = vaccine.c_adjuvant
    SET vn.STORAGE = vaccine.c_storage
    SET vn.VIRULENCE = vaccine.c_virulence
    SET vn.ANTIGEN = vaccine.c_antigen
    SET vn.ALLERGEN = vaccine.c_allergen
    SET vn.PRESERVATIVE = vaccine.c_preservative
    SET vn.CONTRAINDICTATION = vaccine.c_contraindication
    SET vn.USAGE_AGE = vaccine.c_usage_age
    SET vn.VECTOR = vaccine.c_vector
    SET vn.CURATION_FLAG = vaccine.c_curation_flag
    SET vn.CVX_CODE = vaccine.c_cvx_code
    SET vn.CVX_DESC = vaccine.c_cvx_desc
"""
    tx.run(query, vaccine_batch_data=vaccine_batch_data)


def insert_vaccine_data(model, debug_mode): 
    vaccine_file_name_input = input("Enter the file name of the data in data folder: \n")
    vaccine_file_path = f"data\{vaccine_file_name_input}"
    error_count = 0
    error_lines = []
    try:
        with open(vaccine_file_path, "r", encoding="utf-8") as vaccine_file:
            print("File Opened!")
            vaccine_batch_data = []
            
            vaccine_start_time = time.time()

            vaccine_reader = csv.DictReader(vaccine_file)
            for index, vaccine_file_row in enumerate(vaccine_reader, start=1):
                try:
                    vaccine_id = vaccine_file_row["c_vaccine_id"]
                    vaccine_name = vaccine_file_row["c_vaccine_name"]
                    vaccine_type = vaccine_file_row["c_type"]
                    vaccine_is_combination = vaccine_file_row["c_is_combination_vaccine"]
                    vaccine_description = vaccine_file_row["c_description"]
                    vaccine_adjuvant = vaccine_file_row["c_adjuvant"]   
                    vaccine_storage = vaccine_file_row["c_storage"]
                    vaccine_pathogen_id = vaccine_file_row["c_pathogen_id"]
                    vaccine_virulence = vaccine_file_row["c_virulence"]
                    vaccine_preparation = vaccine_file_row["c_preparation"]
                    vaccine_brand_name = vaccine_file_row["c_brand_name"]
                    vaccine_full_text = vaccine_file_row["c_full_text"]
                    vaccine_antigen = vaccine_file_row["c_antigen"]
                    vaccine_curation_flag = vaccine_file_row["c_curation_flag"]
                    vaccine_vector = vaccine_file_row["c_vector"]
                    vaccine_manufacturer_list = vaccine_file_row["c_manufacturer"].split(', ')
                    vaccine_contraindication = vaccine_file_row["c_contraindication"]
                    vaccine_status = vaccine_file_row["c_status"]
                    vaccine_location_licensed_list = vaccine_file_row["c_location_licensed"].split(', ')
                    vaccine_host_species = vaccine_file_row["c_host_species"]
                    vaccine_route_list = vaccine_file_row["c_route"].split(', ')
                    vaccine_vo_id = vaccine_file_row["c_vo_id"]
                    vaccine_usage_age = vaccine_file_row["c_usage_age"]
                    vaccine_model_host = vaccine_file_row["c_model_host"]
                    vaccine_preservative = vaccine_file_row["c_preservative"]
                    vaccine_allergen = vaccine_file_row["c_allergen"]
                    vaccine_preparation_vo_id = vaccine_file_row["c_preparation_vo_id"]
                    vaccine_host_spcecies_2 = vaccine_file_row["c_host_species2"]
                    vaccine_cvx_code = vaccine_file_row["c_cvx_code"]
                    vaccine_cvx_desc = vaccine_file_row["c_cvx_desc"]
                    vaccine_proper_name = vaccine_file_row["c_proper_name"]
                    
                    if vaccine_model_host:
                        generated_model_host_range = host_id_creation_for_unstructured_hosts(vaccine_model_host, model=model, debug_mode=debug_mode)
                    else:
                        generated_model_host_range = vaccine_model_host



                    vaccine_batch_data.append({
                        "c_vaccine_id": vaccine_id,
                        "c_vaccine_name": vaccine_name,
                        "c_type": vaccine_type,
                        "c_is_combination_vaccine": vaccine_is_combination,
                        "c_description": vaccine_description,
                        "c_adjuvant": vaccine_adjuvant,
                        "c_storage": vaccine_storage,
                        "c_pathogen_id": vaccine_pathogen_id,
                        "c_virulence": vaccine_virulence,
                        "c_preparation": vaccine_preparation,
                        "c_brand_name": vaccine_brand_name,
                        "c_full_text": vaccine_full_text,
                        "c_antigen": vaccine_antigen,
                        "c_curation_flag": vaccine_curation_flag,
                        "c_vector": vaccine_vector,
                        "c_manufacturer": vaccine_manufacturer_list,
                        "c_contraindication": vaccine_contraindication,
                        "c_status": vaccine_status,
                        "c_location_licensed": vaccine_location_licensed_list,
                        "c_host_species": vaccine_host_species,
                        "c_route": vaccine_route_list,
                        "c_vo_id": vaccine_vo_id,
                        "c_usage_age": vaccine_usage_age,
                        "c_model_host": generated_model_host_range,
                        "c_preservative": vaccine_preservative,
                        "c_allergen": vaccine_allergen,
                        "c_preparation_vo_id": vaccine_preparation_vo_id,
                        "c_host_species2": vaccine_host_spcecies_2,
                        "c_cvx_code": vaccine_cvx_code,
                        "c_cvx_desc": vaccine_cvx_desc,
                        "c_proper_name": vaccine_proper_name,
                    })
                    if debug_mode:
                        print(f"""{vaccine_name} with id {vaccine_id} and {vaccine_vo_id} has the manufacter(s) {vaccine_manufacturer_list}\n
                        Licensed in {vaccine_location_licensed_list} and goes through routes {vaccine_route_list}
                        Description: {vaccine_description}""")
                
                except Exception as e:
                    print(f"\nERROR ~~~ {e} ~~~ ERROR\n")
                    error_count += 1
                    error_lines.append(index)
                
                if len(vaccine_batch_data) >= 10:
                    with driver.session() as session:
                        session.execute_write(batch_insert_vaccine, vaccine_batch_data)
                        vaccine_batch_data.clear()
                        print(f"Inserted The Batch, Current Count Inserted: {index-error_count}")
            if vaccine_batch_data:
                with driver.session() as session:
                    session.execute_write(batch_insert_vaccine, vaccine_batch_data)
                    vaccine_batch_data.clear()
                    print(f"Inserted Last Batch!!!")
            vaccine_end_time = time.time()
            print(f"""Inserted {index-error_count} Lines Sucessfully in {vaccine_end_time-vaccine_start_time}\n
            Had {error_count} Errors, Sucess Rate = {(index-error_count)/index* 100}%\n
            Lines That Failed Insertion: {error_lines}""")
    except Exception as e:
        print(f"ERROR ~~~ {e} ~~~ ERROR")


#VaxGPT
######################################################################################################

def VaxGPT(model, debug_mode):
    pass

def user_query_to_cypher_query(user_input, model, debug_mode):
    cypher_query_generation_template = ChatPromptTemplate([
        ("system", """
        You are a helpful assistant that rewrites user queries into Cypher queries for a Neo4j Vaccine database. 
        Include both nodes, relationships, and relevant properties in the queries. Use a default limit of 5 if the user does not specify.
        
        -Node Types and Properties:
        - DiseaseName: (name)
        - HostName:(HOST_ID, HOST_SCIENTIFIC_NAME, HOST_TAXONOMY_ID, name)
        - PathogenName: (GRAM, PATHOGENESIS, PATHOGEN_ID, PATHOGEN_TAXONOMY_ID, PREPARATION_VO_ID, PROTECTIVE_IMMUNITY, PROTEIN_VO_ID, VACCINE_VO_ID, name)
        - PathogenType: (name)
        - VaccineCountryLicensed: (name)
        - VaccineDeliveryMethod (name)
        - VaccineManufacturer: (name)
        - VaccineName: (name)
        - VaccineStatus: (name)
        - VaccineType
        """)
    ])

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