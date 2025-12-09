document.addEventListener("DOMContentLoaded", function() {
  const messagesElement = document.getElementById("django-messages");
  if (messagesElement) {
    try {
      const djangoMessages = JSON.parse(messagesElement.textContent);
      djangoMessages.forEach(msg => {
        console.log("Auto-toast:", msg.text, msg.type);
        showToast(msg.text, msg.type);
      });
    } catch (e) {
      console.error("Error parsing Django messages:", e);
    }
  }
});
