const skillToggles = [];
// Funcion para enviar peticion de toggle
function toggleSkill(skillName) {
    fetch(`toggle/${skillName}`)
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(error => console.error('Error:', error));
}
// Funcion para actualizar estado de los botones
function updateToggleButtons() {
    const skillsList = document.getElementById('skills-list');
    const toggleButtons = skillsList.querySelectorAll('button');
    toggleButtons.forEach(button => {
        const skillName = button.dataset.skill;
        fetch(`estado.json`)
            .then(response => response.json())
            .then(data => {
                const skillEstado = data.skills[skillName];
                button.textContent = skillEstado ? 'Desactivar' : 'Activar';
            })
            .catch(error => console.error('Error:', error));
    });
}
// Agregar botones de toggle junto a la lista de skills
document.addEventListener('DOMContentLoaded', function() {
    const skillsList = document.getElementById('skills-list');
    const skills = skillsList.querySelectorAll('li');
    skills.forEach(skill => {
        const button = document.createElement('button');
        button.dataset.skill = skill.textContent;
        button.onclick = function() {
            toggleSkill(skill.textContent);
            updateToggleButtons();
        };
        skill.appendChild(button);
    });
});