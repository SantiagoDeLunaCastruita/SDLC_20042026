from flask import Flask, request, render_template, redirect, url_for, session, g
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'nutri_clave_2026'

# --- CONFIGURACIÓN (Herramienta 9) ---
MONGO_URI = 'mongodb://127.0.0.1:27017/'
DATABASE_NAME = 'gestor_tareas'

# --- CLASE GESTOR (Herramientas 7.4, 7.5 y 8) ---
class GestorNutricion:
    def __init__(self, cliente):
        self.cliente = cliente
        self.db = self.cliente[DATABASE_NAME]
        self.usuarios = self.db['usuarios']
        self.tareas = self.db['tareas']
        
        # 7.4 Índices: Asegurar que el email sea único y las tareas rápidas de buscar
        self.usuarios.create_index("email", unique=True)
        self.tareas.create_index([("usuario_id", 1), ("fecha_creacion", -1)])

    def registrar_usuario(self, nombre, email, password):
        """Crea un usuario nuevo"""
        try:
            self.usuarios.insert_one({
                "nombre": nombre,
                "email": email,
                "password": password,
                "fecha_registro": datetime.now()
            })
            return True
        except DuplicateKeyError:
            return False

    def login_usuario(self, email, password):
        """7.5 Proyección: Traemos el ID y Nombre para la sesión"""
        return self.usuarios.find_one(
            {"email": email, "password": password},
            {"nombre": 1, "_id": 1}
        )

    def obtener_tareas_usuario(self, usuario_id):
        """Busca todas las tareas de un usuario específico"""
        tareas = list(self.tareas.find({"usuario_id": ObjectId(usuario_id)}))
        for t in tareas:
            t['_id'] = str(t['_id']) # Convertimos ID para el HTML
        return tareas

# --- GESTIÓN DE CONEXIÓN CON 'G' (Herramienta 9) ---
def get_gestor():
    if 'db_cliente' not in g:
        g.db_cliente = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        g.gestor = GestorNutricion(g.db_cliente)
    return g.gestor

@app.teardown_appcontext
def close_connection(exception):
    cliente = g.pop('db_cliente', None)
    if cliente is not None:
        cliente.close()

# --- RUTAS DE LA APLICACIÓN ---

@app.route('/')
def index():
    # Si ya está logueado, mandarlo directo a sus tareas
    if 'usuario_id' in session:
        return redirect(url_for('ver_tareas'))
    return render_template('index.html')

@app.route('/sesion', methods=['POST'])
def inicio_sesion():
    email = request.form.get('email')
    password = request.form.get('password')
    
    try:
        gestor = get_gestor()
        usuario = gestor.login_usuario(email, password)
        
        if usuario:
            # Guardamos datos importantes en la sesión
            session['usuario_id'] = str(usuario['_id'])
            session['usuario_nombre'] = usuario['nombre']
            return redirect(url_for('ver_tareas'))
    except Exception as e:
        print(f"Error: {e}")
        
    return redirect(url_for('index'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    mensaje = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            gestor = get_gestor()
            if gestor.registrar_usuario(nombre, email, password):
                return redirect(url_for('index'))
            else:
                mensaje = "El correo ya está registrado."
        except:
            mensaje = "Error de conexión con la base de datos."
            
    return render_template('registro.html', mensaje=mensaje)

@app.route('/tareas')
def ver_tareas():
    """Página protegida: Gestor de Tareas"""
    if 'usuario_id' not in session:
        return redirect(url_for('index'))
    
    gestor = get_gestor()
    mis_tareas = gestor.obtener_tareas_usuario(session['usuario_id'])
    return render_template('tareas.html', tareas=mis_tareas)

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)