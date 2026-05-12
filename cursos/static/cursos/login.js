const passwordInput = document.querySelector('#id_password');
const togglePassword = document.querySelector('#toggle-password');

if (passwordInput && togglePassword) {
    togglePassword.addEventListener('click', () => {
        const showingPassword = passwordInput.type === 'text';
        passwordInput.type = showingPassword ? 'password' : 'text';
        togglePassword.textContent = showingPassword ? 'Ver' : 'Ocultar';
        togglePassword.setAttribute('aria-label', showingPassword ? 'Mostrar senha' : 'Ocultar senha');
    });
}
