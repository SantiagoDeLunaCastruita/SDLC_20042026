from flask import Flask, request, render_template, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'nutri_clave_2026'

# --- CONEXIÓN A MONGODB ---
try:
    cliente = MongoClient('mongodb://127.0.0.1:27017/', serverSelectionTimeoutMS=1500)
    db = cliente['gestor_tareas']
    usuarios_col = db['usuarios']
    cliente.admin.command('ping')
    mongo_activo = True
except:
    mongo_activo = False

@app.route('/')
def index():
    logueado = 'usuario_nombre' in session
    return render_template('index.html', logueado=logueado)

@app.route('/sesion', methods=['POST'])
def inicio_sesion():
    email = request.form.get('email')
    password = request.form.get('password')
    if mongo_activo:
        usuario = usuarios_col.find_one({"email": email, "password": password})
        if usuario:
            session['usuario_nombre'] = usuario.get('nombre', 'Usuario')
    return redirect(url_for('index'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    mensaje = None
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if mongo_activo:
            if usuarios_col.find_one({"email": email}):
                mensaje = "El correo ya está registrado."
            else:
                usuarios_col.insert_one({"nombre": nombre, "email": email, "password": password})
                return redirect(url_for('index'))
        else:
            mensaje = "Error: Base de datos no disponible."
            
    return render_template('registro.html', mensaje=mensaje)

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    mensaje = None
    tipo = "info"
    if request.method == 'POST':
        email = request.form.get('email')
        if mongo_activo and usuarios_col.find_one({"email": email}):
            mensaje = f"Enlace enviado a {email}"
            tipo = "success"
        else:
            mensaje = "Correo no encontrado."
            tipo = "danger"
    return render_template('recuperar.html', mensaje=mensaje, tipo=tipo)

@app.route('/salir')
def salir():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)