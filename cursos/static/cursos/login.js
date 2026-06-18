const passwordInput = document.querySelector('#id_password');
const togglePassword = document.querySelector('#toggle-password');
const iconEye = document.querySelector('#icon-eye');
const iconEyeOff = document.querySelector('#icon-eye-off');

if (passwordInput && togglePassword) {
    togglePassword.addEventListener('click', () => {
        const showingPassword = passwordInput.type === 'text';
        passwordInput.type = showingPassword ? 'password' : 'text';
        if (iconEye)    iconEye.style.display    = showingPassword ? '' : 'none';
        if (iconEyeOff) iconEyeOff.style.display = showingPassword ? 'none' : '';
        togglePassword.setAttribute('aria-label', showingPassword ? 'Mostrar senha' : 'Ocultar senha');
    });
}
