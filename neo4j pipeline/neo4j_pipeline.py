import os
import time
from neo4j import GraphDatabase
from dotenv import load_dotenv
import re
import csv


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
        1 - Insert Host Data
        d - Debug Mode
        q - Quit
    """)
    if user_choice.lower() not in ['1', 'q', 'd']:
        print("\nERROR ~~~ INVALID CHOICE ~~~ ERROR\n")
    if user_choice == 'd':
        print(f"Debug Mode Is Now: {not debug_mode}")
        return 1
    if user_choice == '1':
        insert_host_data(debug_mode)
    if user_choice.lower() == 'q':
        return False

def connect_to_neo4j_DB():
    load_dotenv("neo4j_pipeline.env")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    global driver
    driver = GraphDatabase.driver(uri, auth=(user, password))
    print("Connection Sucessful!!!")


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
        tx.run(query, host_batch_data = host_batch_data)

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
                    print("\nERROR ~~~ Failed To Retrieve Data - Is Formatting Wrong? ~~~ ERROR")
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


#Main
######################################################################################################

def main():
    debug_mode = False
    welcome()
    connect_to_neo4j_DB()
    while True:
        menu_choice = menu_selection(debug_mode)
        if menu_choice == '1':
            debug_mode = not debug_mode
        if menu_choice == False:
            break

if __name__ == "__main__":
    main()