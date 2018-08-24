
if (document.querySelector('.formError') != null) {
    let errors = document.querySelectorAll('.formError');
    errors.forEach(function(error) {
        setTimeout(function(){
            error.remove();
        },5000);
    })
}
