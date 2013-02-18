$.fn.autogrow = function() {

    this.filter('textarea').each(function() {

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
            $(this).css('height', Math.max(shadow.height() + 20, minHeight));
        }

        $(this).change(update).keyup(update).keydown(update);

        update.apply(this);

    });

    return this;
};

var previewWindowObject;

function issueSaveAjax(id, redirect){
    var ptitle   = $("#post_title").val();
    var pcontent = $("#post_content").val();

    if (!redirect && !isActive){
        // If its not a redirect (meaning the button was clicked) and the window is
        // not active then do nothing.
        return
    }

    var ajax_req = $.ajax({
        type: "POST",
        url:"/admin/save/"+id,
        data: {title: ptitle,
               content: pcontent}
    });


    if (previewWindowObject == null){
        if (redirect) previewWindowObject = window.open("/preview/"+id, "previewWindow");
    } else {
        ajax_req.done(function(data){
            if (data.update == true){
                var old_scroll_top = $(previewWindowObject).scrollTop();
                previewWindowObject.refreshPreviewPage();
                $(previewWindowObject).scrollTop(old_scroll_top);
                if (redirect){ previewWindowObject.focus(); }
            }
        });
    }
}

var isActive;

$(window).focus(function(){
    isActive = true;
    $("#AutoSaveDetail").css('color','').text('AutoSave: On');
}).blur(function(){
        isActive = false;
        $("#AutoSaveDetail").css('color','red').text('AutoSave: Off');
    });

$(document).ready(function() {
        $("#post_content").autogrow();
    }
);
