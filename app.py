from flask import Flask, render_template, request

app = Flask(__name__)

# 🔸 Lista de proyectos (puedes reemplazarla luego por una base de datos)
proyectos = [
    {'nombre': 'Proyecto 1', 'autor': 'Juan Perez', 'precio': 30, 'valoracion': 4, 'categoria': 'Software'},
    {'nombre': 'Proyecto 2', 'autor': 'Juan Perez', 'precio': 25, 'valoracion': 3, 'categoria': 'Ilustracion'},
    {'nombre': 'Proyecto 3', 'autor': 'Ana Lopez', 'precio': 40, 'valoracion': 5, 'categoria': 'Negocios'},
    {'nombre': 'Proyecto 4', 'autor': 'Luis Ramos', 'precio': 35, 'valoracion': 2, 'categoria': 'Diseno'},
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/acerca')
def acerca():
    return render_template('acerca.html')

@app.route('/explorar')
def explorar():
    # 🔎 Obtener filtros desde la URL
    categoria = request.args.get('categoria')
    orden = request.args.get('orden')

    filtrados = proyectos

    # 📁 Filtro por categoría
    if categoria:
        filtrados = [p for p in filtrados if p['categoria'] == categoria]

    # 📂 Ordenamiento
    if orden == 'precio':
        filtrados = sorted(filtrados, key=lambda p: p['precio'])
    elif orden == 'valoracion':
        filtrados = sorted(filtrados, key=lambda p: p['valoracion'], reverse=True)

    return render_template('explorar.html', proyectos=filtrados, categoria=categoria, orden=orden)

if __name__ == '__main__':
    app.run(debug=True)

