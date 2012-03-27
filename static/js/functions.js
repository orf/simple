function makeExpandingArea(container) {
    var area = container.querySelector('textarea'),
            span = container.querySelector('span');

    if (area.addEventListener) {
        area.addEventListener('input', function() {
            span.textContent = area.value;
        }, false);
        span.textContent = area.value;
    } else if (area.attachEvent) {
        // IE8 compatibility
        area.attachEvent('onpropertychange', function() {
            span.innerText = area.value;
        });
        span.innerText = area.value;
    }

    // Enable extra CSS
    container.className += ' active';
}

function issueSaveAjax(id, redirect){
    var ptitle   = $("#post_title").val();
    var pcontent = $("#post_content").val();
    var req = $.ajax({
        type: "POST",
        url:"/admin/save/"+id,
        data: {title: ptitle,
               content: pcontent}
    });
    req.done(function(message)
    {
        if (redirect)
        {
            var win = window.open("/preview/"+id, '_blank');
        }
    })
}

$(function() {
    var textarea = document.getElementById("post_content");

    if (textarea) {
        textarea.onkeydown = function() {
            textarea.style.height = ""; /* Reset the height*/
            textarea.style.height = textarea.scrollHeight + "px";
        };
    }
});

$(function() {
    // Auto-expanding height for editor textareas
    var areas = document.querySelectorAll('.expandingArea');
    var l = areas.length;

    while (l--) {
        makeExpandingArea(areas[l]);
    }

    // Set minimum height of content textarea
    $('#post_content').css('min-height', $(window).height() - $('#post_title').height() - 130);
});