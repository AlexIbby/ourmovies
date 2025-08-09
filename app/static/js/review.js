(function () {
  function initRating(root = document) {
    root.querySelectorAll('[data-rating-container]').forEach(container => {
      if (container.__ratingBound) return;
      container.__ratingBound = true;

      const stars = container.querySelectorAll('[data-star]');

      function sync(rating) {
        stars.forEach(star => {
          const v = Number(star.dataset.star);
          star.classList.toggle('is-selected', v <= rating);
        });
      }

      function getCurrentRating() {
        const checked = container.querySelector('input[name="rating"]:checked');
        return checked ? Number(checked.value) : 0;
      }

      container.addEventListener('click', e => {
        const star = e.target.closest('[data-star]');
        if (!star || !container.contains(star)) return;
        const val = star.dataset.star;
        const input = container.querySelector(`input[name="rating"][value="${val}"]`);
        if (input) {
          input.checked = true;
          input.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });

      container.addEventListener('mouseover', e => {
        const star = e.target.closest('[data-star]');
        if (star) sync(Number(star.dataset.star));
      });

      container.addEventListener('mouseleave', () => sync(getCurrentRating()));

      container.addEventListener('change', e => {
        if (e.target.matches('input[name="rating"]')) sync(getCurrentRating());
      });

      // Initial hydration for edit form
      sync(getCurrentRating());
    });
  }

  function initTags(root = document) {
    root.querySelectorAll('[data-tags-container]').forEach(container => {
      if (container.__tagsBound) return;
      container.__tagsBound = true;

      function syncOne(cb) {
        const label = container.querySelector(`[data-tag-label="${cb.value}"]`);
        if (label) label.classList.toggle('is-selected', cb.checked);
      }
      function syncAll() {
        container.querySelectorAll('input[type="checkbox"][name="tags"]').forEach(syncOne);
      }

      container.addEventListener('change', e => {
        if (e.target.matches('input[type="checkbox"][name="tags"]')) {
          syncOne(e.target);
        }
      });

      // Initial hydration (pre-checked tags on edit)
      syncAll();
    });
  }

  // Global re-init (safe to call multiple times)
  window.initReviewUI = function (root) {
    initRating(root);
    initTags(root);
  };

  // Auto-run on initial page load
  document.addEventListener('DOMContentLoaded', () => initReviewUI(document));
  
  // Re-run after HTMX swaps
  document.addEventListener('htmx:afterSwap', (e) => {
    initReviewUI(e.detail.target);
  });
})();
