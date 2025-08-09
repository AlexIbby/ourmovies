document.addEventListener('DOMContentLoaded', function() {
    const ratingStars = document.querySelectorAll('.rating-star');
    
    ratingStars.forEach(star => {
        star.addEventListener('click', async function() {
            const rating = parseInt(this.dataset.rating);
            const movieId = this.closest('.rating-container').dataset.movieId;
            
            try {
                const response = await fetch(`/movie/${movieId}/rate`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ rating })
                });
                
                if (response.ok) {
                    // Update visual state of stars
                    ratingStars.forEach((s, index) => {
                        s.classList.toggle('active', index < rating);
                    });
                }
            } catch (error) {
                console.error('Error updating rating:', error);
            }
        });
    });
});
