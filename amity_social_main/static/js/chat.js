// Function to get the CSRF token
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

// Ensure the document is ready before running the script
$(document).ready(function() {
    console.log("Document is ready!");

    const senderUsername = "{{ sender.username }}";
    const receiverUsername = "{{ receiver.username }}";
    
    // Declare the WebSocket connection only once
    const chatSocket = new WebSocket(
        'ws://' + window.location.host + '/ws/chat/' + senderUsername + '/' + receiverUsername + '/'
    );

    // WebSocket onmessage handler
    chatSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        document.querySelector('#chat-log').innerHTML += ('<b>' + data.sender + ':</b> ' + data.message + '<br>');
    };

    // WebSocket onclose handler
    chatSocket.onclose = function(e) {
        console.error('Chat socket closed unexpectedly');
    };

    // Event handler for message submit button
    document.querySelector('#chat-message-submit').onclick = function(e) {
        const messageInputDom = document.querySelector('#chat-message-input');
        const message = messageInputDom.value;
        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInputDom.value = '';
    };
});
