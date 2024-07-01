// get the Sidebar
var sidebar = document.getElementById("ui_sidebar");

// get the DIV with overlay effect
var overlay = document.getElementById("ui_overlay");

// toggle between showing and hiding the sidebar, and add overlay effect
function w3_open() {
    if (sidebar.style.display == 'none') {
        sidebar.classList.add('w3-show').remove('w3-hide');
        overlay.classList.add('w3-show').remove('w3-hide');
    } else {
        sidebar.classList.add('w3-hide').remove('w3-show');
        overlay.classList.add('w3-hide').remove('w3-show');
    }
}

// tlose the sidebar with the close button
function w3_close() {
    sidebar.classList.add('w3-hide');
    overlay.classList.add('w3-hide');
}

// functionality for form selectors
var formSelectors = document.getElementsByClassName("w3-form-selector");
for (var i = 0; i < formSelectors.length; i++) {
    formSelectors[i].addEventListener('change', function() {
        if (this.checked) {
            var formSelectables = document.getElementsByClassName("w3-form-selectable");
            for (let i = 0; i < formSelectables.length; i++) {
                formSelectables.item(i).classList.add('w3-hide');

                console.log('found selectable');
            }
            
            var selector = this.getAttribute("data-selector");
            if (selector != null) {
                var selectable = document.getElementById(selector);
                if (selectable != null) {
                    selectable.classList.remove('w3-hide');
                }
            }
        }
    });
}