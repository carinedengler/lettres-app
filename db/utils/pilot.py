import sqlite3
import xml2db


db_path = '../lettres.dev.sqlite'
#  ['203961.xml', '203962.xml', '203963.xml']
xml_files = ['203963.xml']



db = sqlite3.connect(db_path)
cursor = db.cursor()
cursor.execute('PRAGMA foreign_keys=ON')

# déjà en base, id 77
# xml2db.insert_ref_data(db, cursor)
# xml2db.insert_letter(db, cursor, xml_file_name)
for xml_file in xml_files:
    print("traitement de "+xml_file)
    xml2db.insert_letter(db, cursor, xml_file)

db.close()

