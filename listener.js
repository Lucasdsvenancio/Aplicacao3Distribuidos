const eventSource = new EventSource('http://localhost:8000/Lucas/stream')

function updateMessage(message){
    const list = document.getElementById('messages')
    const item = document.createElement('p')
    item.textContent = message
    list.appendChild(item)
}

eventSource.addEventListener('new_message', function(e){
    updateMessage(e.data)
})

eventSource.onerror = function (event){
    updateMessage('Server closed connection')
    eventSource.close()
}