var base_url = 'http://localhost:8000'
var stream = document.getElementById('stream_nome')
const eventSource = new EventSource(base_url+'/'+stream+'/stream')

function updateMessage(id, message){
    const list = document.getElementById(id)
    const item = document.createElement('p')
    item.textContent = message
    list.appendChild(item)
}

function request_f(request_url, type, formid){
    var list = $('#'+formid).serializeArray()
    var params = new URLSearchParams()
    $.each(list, function(i, field){
        params.append(field.name, field.value)
    })
    fetch(base_url+request_url + params, {method: type})
    .then(response => response.text())
    .then(response => updateMessage(formid, response))
}

function stream_message(){
    var nome = document.getElementById('stream_nome')
    const eventSource = new EventSource(base_url+'/'+nome+'/stream')
    eventSource.addEventListener('stream_message', function(e){
        updateMessage('messages', e.data)
    })
}

