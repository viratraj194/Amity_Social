// Get the CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

$(document).ready(function() {
    // console.log("Document is ready!");

    // Handle click events for both accept and deny actions
    $('.follow-action').on('click', function(event) {
        event.preventDefault();
        // console.log("Follow action button clicked");

        // Get the URL from the data attribute
        const url = $(this).data('url');
        // console.log("URL:", url);

        // Get the follow request ID from the closest div's ID
        const followRequestId = $(this).closest('div.postActivity').attr('id').split('-').pop();
        // console.log("Follow Request ID:", followRequestId);

        $.ajax({
            type: 'POST',
            url: url,
            data: {
                csrfmiddlewaretoken: getCookie('csrftoken'),
            },
            success: function(response) {
                // console.log("AJAX success response:", response);
                if (response.status === 'accepted' || response.status === 'denied' || response.status === 'already_handled') {
                    // Remove the follow request item from the DOM
                    $('#follow-request-' + followRequestId).remove();
                } else {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            title: 'Notice',
                            text: response.message || 'An error occurred',
                            icon: 'info',
                            iconColor: '#fd8925',
                            background: '#0f0f0f',
                            color: '#ffffff',
                            backdrop: `rgba(9, 6, 17, 0.85) backdrop-filter backdrop-blur-sm`,
                            confirmButtonText: 'OK',
                            buttonsStyling: false,
                            customClass: {
                                popup: 'border border-white/10 rounded-3xl shadow-2xl',
                                title: 'text-2xl font-bold',
                                htmlContainer: 'text-[#9ca3af]',
                                confirmButton: 'bg-gradient-to-r from-[#fd8925] to-[#ff0c00] text-white px-8 py-3 rounded-full font-semibold hover:scale-105 transition-transform duration-300 shadow-lg shadow-[#fd8925]/20 mt-4'
                            }
                        });
                    } else {
                        alert('An error occurred');
                    }
                }
            },
            error: function(xhr, status, error) {
                // console.error("AJAX error:", status, error);
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        title: 'Error',
                        text: 'An error occurred. Please try again.',
                        icon: 'error',
                        iconColor: '#fd8925',
                        background: '#0f0f0f',
                        color: '#ffffff',
                        backdrop: `rgba(9, 6, 17, 0.85) backdrop-filter backdrop-blur-sm`,
                        confirmButtonText: 'OK',
                        buttonsStyling: false,
                        customClass: {
                            popup: 'border border-white/10 rounded-3xl shadow-2xl',
                            title: 'text-2xl font-bold',
                            htmlContainer: 'text-[#9ca3af]',
                            confirmButton: 'bg-gradient-to-r from-[#fd8925] to-[#ff0c00] text-white px-8 py-3 rounded-full font-semibold hover:scale-105 transition-transform duration-300 shadow-lg shadow-[#fd8925]/20 mt-4'
                        }
                    });
                } else {
                    alert('An error occurred');
                }
            }
        });
    });
});


// search box showing 
document.addEventListener("DOMContentLoaded", function() {
    // Show the div with class searchUserHtml when clicking on elements with classes searchUsersByUID and searchUsersByPhoneUID
    const searchUserBtns = document.querySelectorAll(".searchUsersByUID, .searchUsersByPhoneUID"); // Select both elements
    const closeBtn = document.getElementById("searchUsers-close");

    // Loop through the selected elements and add event listeners to each
    searchUserBtns.forEach(function(button) {
        button.addEventListener("click", function() {
            // console.log('working');
            document.querySelector(".searchUserHtml").style.display = "block";
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener("click", function() {
            document.querySelector(".searchUserHtml").style.display = "none";
        });
    }
});


// Notification showing for the phone 
// search box showing 
document.addEventListener("DOMContentLoaded", function() {
    // Show the div with class searchUserHtml when clicking on elements with classes searchUsersByUID and searchUsersByPhoneUID
    const searchUserBtns = document.querySelectorAll(".notificationBell"); // Select both elements
    const closeBtn = document.getElementById("notification-close");

    // Loop through the selected elements and add event listeners to each
    searchUserBtns.forEach(function(button) {
        button.addEventListener("click", function() {
            // console.log('working');
            document.querySelector(".postingPageLast").style.display = "block";
        });
    });

    if (closeBtn) {
        closeBtn.addEventListener("click", function() {
            document.querySelector(".postingPageLast").style.display = "none";
        });
    }
});

// Notification showing for the phone 
