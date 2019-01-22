
if (document.querySelector('.formError') != null) {
    let errors = document.querySelectorAll('.formError');
    errors.forEach(function(error) {
        setTimeout(function(){
            error.remove();
        },5000);
    })
}
function Global() {
  this.groupNav = document.querySelector('.groupNav');
}
let g = new Global();
g.groupNav.addEventListener('mouseout', hideGroupsNav);
g.groupNav.addEventListener('mouseover', showGroupsNav);

function hideGroupsNav(e) {
  document.querySelector('.navSubList').style.display = 'none';
}

function showGroupsNav(e) {
  document.querySelector('.navSubList').style.display = 'block';
  document.querySelector('.navSubList').style.zIndex = '9999';
}
