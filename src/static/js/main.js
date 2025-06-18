// Funcionalidad de ordenación
document.addEventListener('DOMContentLoaded', function() {
    // Configuración global para AJAX
    function getCsrfToken() {
        return document.querySelector('meta[name="csrf-token"]').content;
    }

    // Ordenación de artworks
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('sort', this.value);
            window.location.href = currentUrl.toString();
        });
    }

    // Funcionalidad de likes
    const likeBtns = document.querySelectorAll('.like-btn');
    likeBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const artworkId = this.dataset.artworkId;
            fetch(`/artwork/${artworkId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const icon = this.querySelector('i');
                    const likesCount = this.querySelector('.likes-count');
                    
                    if (data.liked) {
                        icon.classList.remove('far');
                        icon.classList.add('fas', 'text-danger');
                    } else {
                        icon.classList.remove('fas', 'text-danger');
                        icon.classList.add('far');
                    }
                    
                    likesCount.textContent = data.likes_count;
                }
            })
            .catch(error => console.error('Error:', error));
        });
    });
}); 