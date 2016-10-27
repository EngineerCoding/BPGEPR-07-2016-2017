#!/usr/python
import psycopg2
from os import system


def prep_inserting():
    system('bash deelopdracht\\ B')
    # Execute CREATE statements


def insert_data(cursor, table, lst_data):
    """ Inserts data based on the table name and a list of
    dictionaries which represent a row which should be 
    inserted.

    Parameters:
        cursor - Cursor object. The connection cursor which executes
        the query
        table - string. The table name to insert into.
        lst_data - list. This list should contain dictionaries which
        represent a row with the correct columns.
    Return:
        Nothing.
    """
    query = 'INSERT INTO {} ({}) VALUES ({});'
    for query_data in lst_data:
        # Create lists with the column names and values
        columns = []
        values = []
        for column in query_data:
            columns.append(column)
            values.append(query_data[column])
        # Generate the columns string for the query
        columns = ", ".join(columns)
        # Generate the values string for the query
        values = '\'{}\''.format('\', \''.join(values))
        cursor.execute(query.format(table, columns, values))
    # Commit the insertions in one batch
    cursor.commit()


def insert_gene_exon(cursor):
    pass


def insert_protein_reactions(cursor):
    pass


def insert_pathway_domains(cursor):
    pass


def main():
    prep_inserting()
    connection = pscyopg2.connect(host="localhost", dbname="dbname", user="postgres", password="BiOLaB15")
    cursor = connection.cursor()
    insert_gene_exon(cursor)
    insert_protein_reactions(cursor)
    insert_pathway_domains(cursor)
