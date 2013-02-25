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

function issueSaveAjax(id){
    if (!isActive){
        // If the window is not active do nothing, prevents useless auto-saves.
        return
    }

    $.ajax({
        type: "POST",
        url:"/admin/save/"+id,
        data: {title: $("#post_title").val(),
               content: $("#post_content").val()}
    });
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
