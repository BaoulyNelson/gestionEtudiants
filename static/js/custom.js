// Scripts personnalisés
document.addEventListener('DOMContentLoaded', function() {
    // Confirmation avant suppression
    document.querySelectorAll('[data-confirm]').forEach(function(element) {
        element.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
});