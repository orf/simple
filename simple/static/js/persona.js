$(function() {
  /* convert the links into clickable buttons that go to the
     persona service */
  $('a.login-btn').on('click', function() {
    navigator.id.request({
      siteName: $SITENAME
    });
    return false;
  });

  $('a.logout-button').on('click', function() {
    navigator.id.logout();
    return false;
  });

  /* watch persona state changes */
  navigator.id.watch({
    loggedInUser: $CURRENT_USER,
    onlogin: function(assertion) {
      /* because the login needs to verify the provided assertion
         with the persona service which requires an HTTP request,
         this could take a bit.  To not confuse the user we show
         a progress box */
      var box = $('<div class=signinprogress></div>')
        .hide()
        .text('Please wait ...')
        .appendTo('body')
        .fadeIn('fast');
      $.ajax({
        type: 'POST',
        url: $URL_ROOT + '_auth/login',
        data: {assertion: assertion, _csrf_token: $CSRF},
        success: function(res, status, xhr) { window.location.reload(); },
        error: function(xhr, status, err) {
          box.remove();
          navigator.id.logout();
          alert('Login failure: ' + err);
        }
      });
    },
    onlogout: function() {
      $.ajax({
        type: 'POST',
        url: $URL_ROOT + '_auth/logout',
        data: {_csrf_token: $CSRF },
        success: function(res, status, xhr) { window.location.reload(); },
        error: function(xhr, status, err) {
          alert('Logout failure: ' + err);
        }
      });
    }
  });
});