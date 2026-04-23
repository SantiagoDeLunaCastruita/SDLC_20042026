from flask import Flask, request, render_template, redirect, url_for, session, g
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nutri_clave_2026'

MONGO_URI = 'mongodb://127.0.0.1:27017/'
DATABASE_NAME = 'gestor_tareas'

# --- CLASE GESTOR (Herramienta 8 y 7.4) ---
class GestorNutricion:
    def __init__(self, cliente):
        self.cliente = cliente
        self.db = self.cliente[DATABASE_NAME]
        self.usuarios = self.db['usuarios']
        self.tareas = self.db['tareas']
        # Índices apropiados
        self.usuarios.create_index("email", unique=True)
        self.tareas.create_index([("usuario_id", 1), ("fecha_creacion", -1)])

    def login_usuario(self, email, password):
        # 7.5 Proyección para eficiencia
        return self.usuarios.find_one(
            {"email": email, "password": password},
            {"nombre": 1, "_id": 1} # Necesitamos el _id para las tareas
        )

    def obtener_tareas_usuario(self, usuario_id):
        """Herramienta 8: Obtener tareas filtradas"""
        tareas = list(self.tareas.find({"usuario_id": ObjectId(usuario_id)}))
        for t in tareas:
            t['_id'] = str(t['_id'])
        return tareas

# --- GESTIÓN DE CONEXIÓN (Herramienta 9) ---
def get_gestor():
    if 'db_cliente' not in g:
        g.db_cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1500)
        g.gestor = GestorNutricion(g.db_cliente)
    return g.gestor

@app.teardown_appcontext
def close_connection(exception):
    cliente = g.pop('db_cliente', None)
    if cliente is not None:
        cliente.close()

# --- RUTAS ---

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('ver_tareas'))
    return render_template('index.html')

@app.route('/sesion', methods=['POST'])
def inicio_sesion():
    email = request.form.get('email')
    password = request.form.get('password')
    
    gestor = get_gestor()
    usuario = gestor.login_usuario(email, password)
    
    if usuario:
        # Guardamos datos en la sesión
        session['usuario_id'] = str(usuario['_id'])
        session['usuario_nombre'] = usuario['nombre']
        return redirect(url_for('ver_tareas')) # Redirigir a la nueva página
    
    return redirect(url_for('index'))

@app.route('/tareas')
def ver_tareas():
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    
    gestor = get_gestor()
    # Obtenemos las tareas del usuario logueado
    mis_tareas = gestor.obtener_tareas_usuario(session['usuario_id'])
    return render_template('tareas.html', tareas=mis_tareas)

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)