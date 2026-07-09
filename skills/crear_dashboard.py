import sqlite3
from jinja2 import Template

# Conectar a la base de datos
conn = sqlite3.connect('agente_memoria.db')
c = conn.cursor()

# Consultar la tabla 'skills'
c.execute("SELECT nombre, descripcion FROM skills")
skills = c.fetchall()

# Plantilla HTML para el dashboard
template = Template('''
<!DOCTYPE html>
<html(lang='es')>
<head>
    <title>Dashboard de Habilidades</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #333;
            color: #fff;
        }
    </style>
</head>
<body>
    <h1>Dashboard de Habilidades</h1>
    <ul>
    {% for skill in skills %}
        <li>{{ skill[0] }}: {{ skill[1] }}</li>
    {% endfor %}
    </ul>
</body>
</html>
''')

# Generar el archivo 'dashboard.html'
with open('dashboard.html', 'w') as f:
    f.write(template.render(skills=skills))
