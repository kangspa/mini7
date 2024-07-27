$(document).ready(function(){
    $('#chat-form').on('submit', function(event){
        event.preventDefault();
        const question = $('#question').val();
        if (question.trim() !== ''){
            let chatBox = document.getElementById('chatBody');
            chatBox.innerHTML += `<div class="chat-message user-message"><p>${question}</p></div>`;
            $.ajax({
                type: 'POST',
                url: '',
                data: {
                    'question': question,
                    'csrfmiddlewaretoken': $('input[name="csrfmiddlewaretoken"]').val()
                },
                success: function(response) {
                    let context = response.context;
                    let chatBox = document.getElementById('chatBody');
                    
                    chatBox.innerHTML += `<div class="chat-message bot-message"><p>${context.result}</p></div>`;
                },
                error: function(xhr) {
                    console.log(xhr.status + ": " + xhr.responseText);
                }
            });
            $('#question').val('');
        } else {
            alert('질문을 입력해주세요.')
        }
    });
});