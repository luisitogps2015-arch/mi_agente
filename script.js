const cajonTexto = document.getElementById('cajon_texto');
const botonEnviar = document.getElementById('boton_enviar');

botonEnviar.addEventListener('click', () => {
    const texto = cajonTexto.value;
    console.log(`Texto enviado: ${texto}`);
    cajonTexto.value = '';
});

cajonTexto.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault(); // Evita que se haga un salto de línea
        const texto = cajonTexto.value;
        console.log(`Texto enviado: ${texto}`);
        cajonTexto.value = '';
    }
});
