import pandas as pd

def remove_field_from_rows(csv_file, columns, output_file):
    df = pd.read_csv("./preprocessingData/"+csv_file)
    # Sostituisci \N con "" nelle colonne specificate
    df[columns] = df[columns].replace(r'\\N', '', regex=True)
    df.to_csv("./preprocessingData/"+output_file, index=False)

input_file = str(input("Inserisci il nome del file csv:\n"))
output_file = str(input("Inserisci nome file di output:\n"))
fields = str(input("Inserisci i campi:\n"))

fields = fields.split(',')

remove_field_from_rows(input_file, fields, output_file)