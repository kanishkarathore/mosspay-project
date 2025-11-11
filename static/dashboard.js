document.addEventListener('DOMContentLoaded', function() {
    
    // --- Sidebar Toggle Logic (Unchanged) ---
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    function toggleSidebar() {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('open');
    }

    hamburgerBtn.addEventListener('click', toggleSidebar);
    overlay.addEventListener('click', toggleSidebar);

    
    // --- 1. Banner Carousel Logic (NEW) ---
    const track = document.querySelector('.banner-track');
    if (track) {
        // Get all the banner items
        const items = track.querySelectorAll('.banner-item');
        const itemCount = items.length;
        let currentIndex = 0;

        // Set an interval to run every 4 seconds
        setInterval(() => {
            // Move to the next item, looping back to 0
            currentIndex = (currentIndex + 1) % itemCount;
            
            // Apply the CSS transform to slide the whole track
            track.style.transform = `translateX(-${currentIndex * 100}%)`;
        }, 4000); // 4 seconds
    }

});