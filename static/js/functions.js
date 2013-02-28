$.fn.autogrow = function() {

    var scrollOnce = false;

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
            var new_height = Math.max(shadow.height() + $("#publish-bar").outerHeight() + 30, minHeight);
            var old_height = $(this).height();
            $(this).css('height', new_height);
            if (old_height != new_height){
                // Hack: update is fired once on page load, so prevent auto-scrolling once.
                if (scrollOnce == false){
                    scrollOnce = true;
                } else {
                    if (($(window).scrollTop() + $(window).height()) - $(document).height() > -20){
                        $('html, body').animate({scrollTop: $(document).height()}, 'fast')
                    }
                }
            }
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
    $("#auto-save").css('color','').text('Draft');
}).blur(function(){
        isActive = false;
        $("#auto-save").css('color','red').text('Draft *');
    });

$(document).ready(function() {
        $("#post_content").autogrow();
    }
);
