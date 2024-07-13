// postcontainer scroolbar 
document.addEventListener('DOMContentLoaded', function () {
    let postContainer = document.querySelector('.PostContainer');

    // Check if content height exceeds max-height and apply scrollbar
    if (postContainer.scrollHeight > postContainer.clientHeight) {
        postContainer.style.overflowY = 'auto';
    }

})

// pop us posts page 
function redirectToPath(path) {
    window.location.href = path;
}

document.addEventListener('DOMContentLoaded', function () {
    const openButton = document.querySelector('.open');
    const postDiv = document.querySelector('.PostContainers');
    const closeButton = postDiv.querySelector('.close');

    openButton.addEventListener('click', function () {
        postDiv.style.display = 'block';
    });

    closeButton.addEventListener('click', function () {
        if (confirm('Are you sure you want to discard the post?')) {
            postDiv.style.display = 'none';
            redirectToPath('/accounts/list_posts/list-posts/');
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

    userInput.addEventListener('input', () => {
        const text = userInput.value.trim();
        const words = text.split(/\s+/).filter(word => word.length > 0);
        const wordCount = words.length;
        const progress = Math.min(wordCount / 60 * 100, 100);
        const offset = 94.2 - (94.2 * progress / 100);

        progressCircle.style.strokeDashoffset = offset;
        progressText.textContent = `${Math.floor(progress)}%`;

        if (wordCount > 60) {
            progressCircle.classList.add('over-limit');
            alert('Word limit exceeded!');
        } else {
            progressCircle.classList.remove('over-limit');
        }
    });
});





