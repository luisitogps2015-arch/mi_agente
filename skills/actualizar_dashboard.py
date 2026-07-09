const datos = JSON.parse(this.responseText);
const skillsList = document.getElementById('skills-list');

// Limpiar lista anterior
while (skillsList.firstChild) {
    skillsList.removeChild(skillsList.firstChild);
}

// Crear lista dinámica de skills
datos.skills.forEach(skill => {
    const listItem = document.createElement('li');
    listItem.textContent = skill;
    skillsList.appendChild(listItem);
});