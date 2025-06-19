import mysql.connector 
cnx = mysql.connector.connect(user='root', password='shub12345',host="localhost", database='gms')
if cnx.is_connected():
    print("niga")