// 100% stolen from yiransheng/simple
$.fn.autogrow = function(options) {

    this.filter('textarea :not(#post_title)').each(function() {

        var $this       = $(this),
                minHeight   = $this.height(),
                lineHeight  = $this.css('lineHeight');

        var shadow = $('<div></div>').css({
            position:   'absolute',
            top:        -10000,
            left:       -10000,
            width:      $(this).width(),
            fontSize:   $this.css('fontSize'),
            fontFamily: $this.css('fontFamily'),
            lineHeight: $this.css('lineHeight'),
            resize:     'none'
        }).appendTo(document.body);

        var update = function() {

            var val = this.value.replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/&/g, '&amp;')
                    .replace(/\n/g, '<br/>');

            shadow.html(val);
            $(this).css('height', Math.max(shadow.height() + 60, minHeight));
        }

        $(this).change(update).keyup(update).keydown(update);

        update.apply(this);

    });

    return this;

};


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
    var x = document.getElementById("edit_post_area");
    if (x != null) {
        makeExpandingArea(x);
    }
});
