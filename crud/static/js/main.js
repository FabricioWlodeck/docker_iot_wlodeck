document.addEventListener('DOMContentLoaded', () => {
  const boton = document.getElementById('themeToggle');
  if (!boton) return;

  const actualizar_icono = (tema) => {
    boton.textContent = tema === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
  };

  actualizar_icono(document.documentElement.getAttribute('data-bs-theme'));

  boton.addEventListener('click', () => {
    const actual = document.documentElement.getAttribute('data-bs-theme');
    const siguiente = actual === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', siguiente);
    localStorage.setItem('tema', siguiente);
    actualizar_icono(siguiente);
  });
});
