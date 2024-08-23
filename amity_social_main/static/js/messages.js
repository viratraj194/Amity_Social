function scrollToBottom() {
    var chatContainer = document.getElementById("chatContainer");
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Call the function when the page loads
window.onload = function () {
    scrollToBottom();
};

// Retrieve room slug from the template context
const roomSlug = '{{ room.slug }}';

// Determine the correct WebSocket protocol
const websocketProtocol = window.location.protocol === "https:" ? "wss" : "ws";

// Update the WebSocket endpoint to use the room slug
const wsEndpoint = `${websocketProtocol}://${window.location.host}/ws/chat/${roomSlug}/`;

const socket = new WebSocket(wsEndpoint);

socket.onopen = function (event) {
    console.log("WebSocket connection opened");
};

socket.onmessage = function (event) {
    try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        if (data.status) {
            // Handle user status updates
            const userId = data.user_id;
            const status = data.status;

            let statusElement = document.getElementById(`status-${userId}`);

            if (statusElement) {
                // Update existing status element
                statusElement.textContent = status === 'online' ? 'Online' : 'Offline';
            } else {
                // Create a new status element if it doesn't exist
                statusElement = document.createElement('div');
                statusElement.id = `status-${userId}`;
                statusElement.textContent = status === 'online' ? 'Online' : 'Offline';
                statusElement.className = 'userStatus';

                const statusContainer = document.getElementById('statusContainer');
                statusContainer.appendChild(statusElement);
            }
        } else if (data.message) {
            // Handle incoming messages
            const message = data.message;
            const messageSenderId = data.sender_id;
            const senderProfilePic = data.sender_profile_pic;

            // Create a message element
            const messageElement = document.createElement('div');
            const isSender = messageSenderId == '{{ user.id }}'; // Compare with the current user's ID

            if (isSender) {
                messageElement.className = 'senderMessage';
                messageElement.innerHTML = `
                <p>${message}</p>
                <div class="receiverMessageImg">
                    <img src="${senderProfilePic}" alt="">
                </div>
            `;
            } else {
                messageElement.className = 'receiverMessage';
                messageElement.innerHTML = `
                <div class="receiverMessageImg">
                    <img src="${senderProfilePic}" alt="">
                </div>
                <p>${message}</p>
            `;
            }

            const chatContainer = document.getElementById('chatContainer');
            chatContainer.appendChild(messageElement);
            scrollToBottom(); // Scroll to the bottom
        }
    } catch (error) {
        console.error("Error processing WebSocket message:", error);
    }
};

socket.onerror = function (error) {
    console.error("WebSocket error:", error);
};

socket.onclose = function (event) {
    console.log("WebSocket connection closed!");
};

function sendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();

    if (message) {
        socket.send(JSON.stringify({
            'message': message,
            'sender_id': '{{ user.id }}',  // Use the current user's ID
            'sender_profile_pic': '{{ user.userprofile.profile_picture.url }}'
        }));
        messageInput.value = '';
    }
}

document.getElementById('sendMessageButton').addEventListener('click', function (event) {
    event.preventDefault();
    sendMessage();
});

// Optional: Send message on Enter key press
// document.getElementById('messageInput').addEventListener('keypress', function (event) {
//     if (event.key === 'Enter') {
//         event.preventDefault();
//         sendMessage();
//     }
// });
