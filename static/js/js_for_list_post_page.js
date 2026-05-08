document.addEventListener('DOMContentLoaded', function () {
    var swiper = new Swiper('.swiper-container', {
        slidesPerView: 'auto',
        spaceBetween: 10,
        grabCursor: true,
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
    });
});


// comment sections
// Event delegation for toggling comments
document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('Comment-onPost')) {
            e.preventDefault();
            const post_id = e.target.getAttribute('data-id');

            const targetDiv = document.querySelector(`.PostComments-forPosts[data-id="${post_id}"]`);
            if (targetDiv) {
                targetDiv.style.display = targetDiv.style.display === 'block' ? 'none' : 'block';
            }
        }
    });
});
// close the comment section
document.addEventListener('DOMContentLoaded', function () {
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('Comment-Close')) {
            e.preventDefault();
            const post_id = e.target.getAttribute('data-id');
            const targetDiv = document.querySelector(`.PostComments-forPosts[data-id="${post_id}"]`);
            if (targetDiv) {
                targetDiv.style.display = targetDiv.style.display === 'block' ? 'none' : 'block';
            }
        }
    });
});




// pop us posts page
function redirectToPath(path) {
    window.location.href = path;
}

// Mode Toggle - Image Post / Confession
function switchTab(mode) {
    const imageTab = document.getElementById('image-post-view');
    const confessionTab = document.getElementById('confession-post-view');
    const imageLabel = document.getElementById('imageLabel');
    const progressContainer = document.getElementById('confessionProgress');
    const emptyImageState = document.getElementById('emptyImageState');
    const imageInput = document.getElementById('imageInput');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const buttons = document.querySelectorAll('.toggle-btn');

    buttons.forEach(btn => {
        if (btn.getAttribute('data-mode') === mode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    if (mode === 'image') {
        if (imageTab) imageTab.style.display = 'block';
        if (confessionTab) confessionTab.style.display = 'none';
        if (imageLabel) imageLabel.style.display = 'flex'; // Changed to flex for wide button
        if (progressContainer) progressContainer.style.display = 'none';
        
        // Show empty state if no image is selected
        if (imageInput && !imageInput.files.length) {
            if (emptyImageState) emptyImageState.style.display = 'flex';
            if (imagePreviewContainer) imagePreviewContainer.style.display = 'none';
        } else if (imageInput && imageInput.files.length) {
            if (emptyImageState) emptyImageState.style.display = 'none';
            if (imagePreviewContainer) imagePreviewContainer.style.display = 'block';
        }
    } else {
        if (imageTab) imageTab.style.display = 'none';
        if (confessionTab) confessionTab.style.display = 'block';
        if (imageLabel) imageLabel.style.display = 'none';
        if (progressContainer) progressContainer.style.display = 'flex';
        if (emptyImageState) emptyImageState.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const openButtons = document.querySelectorAll('.open'); // Select all elements with the class 'open'
    const postDiv = document.querySelector('.PostContainers');
    const closeButton = postDiv.querySelector('.close');

    // Attach click event listener to each open button
    openButtons.forEach(function (openButton) {
        openButton.addEventListener('click', function () {
            postDiv.style.display = 'flex';
            // Trigger initial tab state
            const activeTab = document.querySelector('.toggle-btn.active');
            if (activeTab) {
                switchTab(activeTab.getAttribute('data-mode'));
            }
        });
    });

    closeButton.addEventListener('click', function () {
        if (confirm('Are you sure you want to discard the post?')) {
            postDiv.style.display = 'none';
        }
    });

    // Image preview functionality
    const imageInput = document.getElementById('imageInput');
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const imagePreview = document.getElementById('imagePreview');
    const removeImageBtn = document.getElementById('removeImageBtn');
    const emptyImageState = document.getElementById('emptyImageState');

    if (imageInput && imagePreviewContainer && imagePreview) {
        imageInput.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    imagePreview.src = event.target.result;
                    imagePreviewContainer.style.display = 'block';
                    imagePreviewContainer.classList.add('has-image');
                    if (emptyImageState) emptyImageState.style.display = 'none';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Remove image button functionality
    if (removeImageBtn && imageInput && imagePreviewContainer && imagePreview) {
        removeImageBtn.addEventListener('click', function () {
            imageInput.value = '';
            imagePreview.src = '';
            imagePreviewContainer.style.display = 'none';
            imagePreviewContainer.classList.remove('has-image');
            if (emptyImageState) emptyImageState.style.display = 'flex';
        });
    }

    // Word counter for Confession mode (60 word limit)
    const userInput = document.getElementById('userInputConfession');
    const progressCircle = document.querySelector('.progress-container .progress');
    const progressText = document.querySelector('.progress-container .text');
    const postButton = document.querySelector('.postButton');

    if (userInput && progressCircle && progressText) {
        userInput.addEventListener('input', function () {
            const text = userInput.value.trim();
            const words = text.split(/\s+/).filter(word => word.length > 0);
            const wordCount = words.length;
            const maxWords = 60;
            const progress = Math.min((wordCount / maxWords) * 100, 100);
            const dashOffset = 157.1 - (157.1 * progress / 100);

            progressCircle.style.strokeDashoffset = dashOffset;
            progressText.textContent = wordCount + '/' + maxWords + ' words';

            // Change color based on progress
            if (wordCount >= maxWords) {
                progressCircle.style.stroke = '#ff4444';
            } else if (wordCount >= maxWords * 0.8) {
                progressCircle.style.stroke = '#ffaa00';
            } else {
                progressCircle.style.stroke = '#2b68ff';
            }

            if (wordCount > maxWords) {
                postButton.disabled = true;
            } else {
                postButton.disabled = false;
            }
        });
    }
});