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
    console.log("Document is ready!");

    // Handle click events for both accept and deny actions
    $('.follow-action').on('click', function(event) {
        event.preventDefault();
        console.log("Follow action button clicked");

        // Get the URL from the data attribute
        const url = $(this).data('url');
        console.log("URL:", url);

        // Get the follow request ID from the closest div's ID
        const followRequestId = $(this).closest('div.postActivity').attr('id').split('-').pop();
        console.log("Follow Request ID:", followRequestId);

        $.ajax({
            type: 'POST',
            url: url,
            data: {
                csrfmiddlewaretoken: getCookie('csrftoken'),
            },
            success: function(response) {
                console.log("AJAX success response:", response);
                if (response.status === 'accepted' || response.status === 'denied') {
                    // Remove the follow request item from the DOM
                    $('#follow-request-' + followRequestId).remove();
                } else {
                    alert('An error occurred');
                }
            },
            error: function(xhr, status, error) {
                console.error("AJAX error:", status, error);
                alert('An error occurred');
            }
        });
    });
});
