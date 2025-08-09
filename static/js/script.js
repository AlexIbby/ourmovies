document.addEventListener('DOMContentLoaded', function() {
    // Star Rating Interaction
    const stars = document.querySelectorAll('.star-rating input[type="radio"]');

    stars.forEach(star => {
        star.addEventListener('change', function() {
            const ratingValue = this.value;
            highlightStars(ratingValue);
        });
    });

    function highlightStars(rating) {
        stars.forEach(star => {
            if (star.value <= rating) {
                star.nextElementSibling.classList.add('active');
            } else {
                star.nextElementSibling.classList.remove('active');
            }
        });
    }

    // Check if there's a pre-selected star rating on page load and highlight accordingly
    const checkedStar = document.querySelector('.star-rating input[type="radio"]:checked');
    if (checkedStar) {
        highlightStars(checkedStar.value);
    }

     // Tag Interaction
     const tags = document.querySelectorAll('.tags-container input[type="checkbox"]');

     tags.forEach(tag => {
         tag.addEventListener('change', function() {
             if (this.checked) {
                 this.nextElementSibling.classList.add('active');
             } else {
                 this.nextElementSibling.classList.remove('active');
             }
         });
     });
 
     // Check if there's pre-selected tags on page load and highlight accordingly
     const checkedTags = document.querySelectorAll('.tags-container input[type="checkbox"]:checked');
     checkedTags.forEach(tag => {
         tag.nextElementSibling.classList.add('active');
     });
});
