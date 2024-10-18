from flask import Flask, request, url_for, render_template, session, redirect
import cx_Oracle
import os
app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')

@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['usuario']  
        password = request.form['password']

        try:
            connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn="192.168.1.147/ORCLCDB"
            )
            connection.close()
            session['usuario'] = username  
            session['password'] = password
        
            return redirect(url_for('tablas'))
        except cx_Oracle.DatabaseError as e:
            error = "Usuario o contraseña no válidos"
            return render_template("login.html", titulo="LOGIN", error=error)
    
    return render_template("login.html", titulo="LOGIN")

@app.route('/tablas', methods=["GET"])
def tablas():
    if 'usuario' in session:
        username = session.get('usuario')  
        password = session.get('password')
        try: 
            connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn="192.168.1.147/ORCLCDB"
            )
            cursor = connection.cursor()
            sql = '''
                SELECT UPPER(t.table_name) AS table_name, UPPER(t.owner) AS creador 
                FROM all_tables t 
                WHERE t.table_name IN (
                    SELECT table_name FROM user_tables
                    UNION ALL
                    SELECT table_name FROM all_tab_privs 
                    WHERE grantee = UPPER(:username) AND privilege = 'SELECT'
                )
            '''

            cursor.execute(sql, username=username)  
            registros = cursor.fetchall()

            return render_template("tablas.html", registros=registros, titulo="TABLAS DISPONIBLES")
        except Exception as e:
            return f"Error al consultar tus tablas: {str(e)}"  
    else:
        return render_template("login.html", titulo="LOGIN")

@app.route('/tablas/<nombre_tabla>', methods=["GET"])
def ver_tabla(nombre_tabla):
    if 'usuario' in session:
        username = session.get('usuario')
        password = session.get('password')
        try:
            connection = cx_Oracle.connect(
                user=username,
                password=password,
                dsn="192.168.1.147/ORCLCDB"
            )
            cursor = connection.cursor()

            sql_creador = '''
                SELECT owner 
                FROM all_tables 
                WHERE table_name = UPPER(:nombre_tabla)
            '''
            cursor.execute(sql_creador, nombre_tabla=nombre_tabla)
            creador = cursor.fetchone()
            if creador:
                creador = creador[0]
            else:
                return f"Tabla {nombre_tabla} no encontrada."

            sql = f'SELECT * FROM {creador}.{nombre_tabla}'
            cursor.execute(sql)
            registros = cursor.fetchall()
            columnas = [desc[0] for desc in cursor.description]

            return render_template("vista_tabla.html", registros=registros, columnas=columnas, titulo=f"Contenido de {nombre_tabla}")
        except Exception as e:
            return f"Error al consultar la tabla: {str(e)}"
    else:
        return render_template("login.html", titulo="LOGIN")

if __name__ == '__main__':
    app.run('0.0.0.0', 5001, debug=True)
