from flask import Flask, render_template, request

app = Flask(__name__)

# 🔸 Lista de proyectos
proyectos = [
    {
        'id': 1,
        'nombre': 'Proyecto 1',
        'autor': 'Juan Perez',
        'precio': 30,
        'valoracion': 4,
        'categoria': 'Software',
        'colaboraciones': 12
    },
    {
        'id': 2,
        'nombre': 'Proyecto 2',
        'autor': 'Juan Perez',
        'precio': 25,
        'valoracion': 3,
        'categoria': 'Ilustracion',
        'colaboraciones': 8
    },
    {
        'id': 3,
        'nombre': 'Proyecto 3',
        'autor': 'Ana Lopez',
        'precio': 40,
        'valoracion': 5,
        'categoria': 'Negocios',
        'colaboraciones': 5
    },
    {
        'id': 4,
        'nombre': 'Proyecto 4',
        'autor': 'Luis Ramos',
        'precio': 35,
        'valoracion': 2,
        'categoria': 'Diseno',
        'colaboraciones': 3
    },
]

@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/acerca')
def acerca():
    return render_template('acerca.html')

@app.route('/explorar')
def explorar():
    categoria = request.args.get('categoria')
    orden = request.args.get('orden')

    filtrados = proyectos

    if categoria:
        filtrados = [p for p in filtrados if p['categoria'] == categoria]

    if orden == 'precio':
        filtrados = sorted(filtrados, key=lambda p: p['precio'])
    elif orden == 'valoracion':
        filtrados = sorted(filtrados, key=lambda p: p['valoracion'], reverse=True)

    return render_template('explorar.html', proyectos=filtrados, categoria=categoria, orden=orden)

@app.route('/proyecto/<int:id>')
def detalle_proyecto(id):
    proyecto = next((p for p in proyectos if p['id'] == id), None)
    if not proyecto:
        return "Proyecto no encontrado", 404
    return render_template('detalle_proyecto.html', proyecto=proyecto)

if __name__ == '__main__':
    app.run(debug=True)


