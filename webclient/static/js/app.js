// get the Sidebar
var sidebar = document.getElementById("ui_sidebar");

// get the DIV with overlay effect
var overlay = document.getElementById("ui_overlay");

// toggle between showing and hiding the sidebar, and add overlay effect
function w3_open() {
    if (sidebar.style.display === 'block') {
        sidebar.style.display = 'none';
        overlay.style.display = "none";
    } else {
        sidebar.style.display = 'block';
        overlay.style.display = "block";
    }
}

// tlose the sidebar with the close button
function w3_close() {
    sidebar.style.display = "none";
    overlay.style.display = "none";
}