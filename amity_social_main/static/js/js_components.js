

// postcontainer scroolbar 

// pop us posts page 
function redirectToPath(path) {
    window.location.href = path;
}

document.addEventListener('DOMContentLoaded', function () {
    const openButtons = document.querySelectorAll('.open'); // Select all elements with the class 'open'
    const postDiv = document.querySelector('.PostContainers');
    const closeButton = postDiv.querySelector('.close');

    // Attach click event listener to each open button
    openButtons.forEach(function (openButton) {
        openButton.addEventListener('click', function () {
            postDiv.style.display = 'block';
        });
    });

    closeButton.addEventListener('click', function () {
        if (confirm('Are you sure you want to discard the post?')) {
            postDiv.style.display = 'none';
        }
    });
});

// Example of using the redirect function if needed





// image auto updating 
document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('imageInput');
    const imageContainer = document.getElementById('preview');

    imageInput.addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                imageContainer.style.display = 'block'; // Show the div
                imageContainer.querySelector('img').src = e.target.result; // Set the image src

            }
            reader.readAsDataURL(file);
        } else {
            imageContainer.style.display = 'none'; // Hide the div if no file is selected
            imageContainer.querySelector('img').src = ''; // Clear the image src
        }
    });
});



// JavaScript code for word count and progress circle
document.addEventListener('DOMContentLoaded', function () {
    const userInput = document.getElementById('userInput');
    const progressCircle = document.querySelector('.progress-circle .progress');
    const progressText = document.querySelector('.progress-circle .text');
    const postButton = document.querySelector('.postButton');
    const moreWordsMessage = document.querySelector('.moreWords');
    let alertShown = false;  // Flag to track if alert message has been shown

    userInput.addEventListener('input', () => {
        const text = userInput.value.trim();
        const words = text.split(/\s+/).filter(word => word.length > 0);
        const wordCount = words.length;
        const progress = Math.min(wordCount / 60 * 100, 100);
        const offset = 94.2 - (94.2 * progress / 100);

        progressCircle.style.strokeDashoffset = offset;
        progressText.textContent = `${Math.floor(progress)}%`;

        // Change circle color based on progress
        if (progress >= 100) {
            progressCircle.classList.add('over-limit');
        } else {
            progressCircle.classList.remove('over-limit');
        }

        // Show/hide postButton based on circle color
        if (progress >= 100) {
            postButton.style.display = 'none';  // Hide the postButton if word count exceeds 60
        } else {
            postButton.style.display = 'block';  // Show the postButton if within word limit
        }

        // Show moreWordsMessage only when progressCircle is over limit and not at 100%
        if (progress >= 100) {
            moreWordsMessage.style.display = 'block';
        } else {
            moreWordsMessage.style.display = 'none';
        }
    });

    // Optional: If you want to handle backspace to reset alertShown and moreWordsMessage
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Backspace') {
            const text = userInput.value.trim();
            const words = text.split(/\s+/).filter(word => word.length > 0);
            const wordCount = words.length;

            if (wordCount <= 60) {
                progressCircle.classList.remove('over-limit');
                postButton.style.display = 'block';  // Show the postButton if within word limit
                moreWordsMessage.style.display = 'none';  // Hide .moreWords message
                alertShown = false;  // Reset alertShown flag
            }
        }
    });
});



// post card swiper 
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
document.addEventListener('DOMContentLoaded', function () {
    $('.Comment-onPost').on('click', function (e) {
        e.preventDefault();
        const post_id = $(this).attr('data-id');

        // Find the div with class 'Comment-container' that has the matching data-id
        const targetDiv = document.querySelector(`.PostComments-forPosts[data-id="${post_id}"]`);

        if (targetDiv) {
            // Toggle the display property
            if (targetDiv.style.display === 'block') {
                targetDiv.style.display = 'none';
            } else {
                targetDiv.style.display = 'block';
            }
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // Get all elements with the class 'comment-close'
    const closeComments = document.getElementsByClassName('comment-close');
    // Get all elements with the class 'PostComments-forPosts'
    const postComments = document.getElementsByClassName('PostComments-forPosts');

    // Add a click event listener to each element with the class 'comment-close'
    for (let i = 0; i < closeComments.length; i++) {
        closeComments[i].addEventListener('click', function () {
            // Hide all elements with the class 'PostComments-forPosts'
            for (let j = 0; j < postComments.length; j++) {
                postComments[j].style.display = 'none';
            }
        });
    }
});



// adding api for the collage name for the profile setting



// if not the profile start
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("deactivateModal");
    const cancelBtn = document.querySelector(".cancel-btn");

    function closeModal() {
        modal.style.display = "none";
    }

    cancelBtn.addEventListener("click", closeModal);

    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });
});


// share event to friend 
