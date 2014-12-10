/*
*   Content Editable Plugin for jQuery with Placeholder
*   Version 1.0.0 (2013-02-15)
*   Plugin website: http://labs.fellipesoares.com/plugins/contenteditable
*   Author: Fellipe Soares Studio
*   Author website: http://www.fellipesoares.com/
*   Dual licensed under the MIT and GPL licenses:
*   http://www.opensource.org/licenses/mit-license.php
*   http://www.gnu.org/licenses/gpl.html
*/
;(function($,window,document){
    
    var updateContent = function(element){
        var c = $(element).html();
        if($.trim($(element).text()) == ''){ c = ''; }
        return c;
    };
    
    $.fn.contentEditable = function(options){
    
        var defaults = {
            'placeholder'           : 'Insert content',
            'newLineOnEnterKey'     : false,
            'onActivate'            : false,
            'onFocusIn'             : false,
            'onFocusOut'            : false,
            'onBlur'                : false
        };
        var settings = $.extend( {}, defaults, options);
        
        return this.each(function() {
            $(this).attr("contenteditable","true");
            this.content = updateContent(this);
            this.settings = settings;
            if(this.content == ''){ $(this).html(settings.placeholder); }
            $(this).on('activate',function(){
                this.content = updateContent(this);
                if(this.content == settings.placeholder){
                    $(this).empty();
                    var range, sel;
                    if ( (sel = document.selection) && document.body.createTextRange) {
                        range = document.body.createTextRange();
                        range.moveToElementText(this);
                        range.select();
                    }
                }
                if($.isFunction(settings.onActivate)){ settings.onActivate(this); }
            })
            .focusin(function(e){
                this.content = updateContent(this);
                if(this.content == settings.placeholder){
                    $(this).empty();
                    var range = document.createRange();
                    range.selectNodeContents(this);
                    var sel = window.getSelection();
                    sel.removeAllRanges();
                    sel.addRange(range);
                }
                if(settings.newLineOnEnterKey == false){
                    $(this).keypress(function(e){
                        var keycode = (e.keyCode ? e.keyCode : e.which);
                        if(keycode == '13') {
                            e.preventDefault();
                            $(this).focusout().blur();
                        }
                    });
                }
                if($.isFunction(settings.onFocusIn)){ settings.onFocusIn(this); }
            })
            .focusout(function(e){
                this.content = updateContent(this);
                $(this).unbind("keypress");
                if(this.content == ''){ $(this).html(settings.placeholder); }
                if($.isFunction(settings.onFocusOut)){ settings.onFocusOut(this); }
            }).blur(function(e){
                if($.isFunction(settings.onBlur)){ settings.onBlur(this); }
            });
        });
    }
})(jQuery,window,document);