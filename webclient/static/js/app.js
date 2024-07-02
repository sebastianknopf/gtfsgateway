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

// converter for FormData to JSON
function form2json(form) {
    let formData = new FormData(form);
    let formDataEntries = formData.entries();
    const handleChild = function (obj, keysArr, value) {
        let firstK = keysArr.shift();
        firstK = firstK.replace(']','');
        if (keysArr.length == 0){
            if (firstK == '') {
                if (!Array.isArray(obj)) obj = [];
                obj.push(value);
            } else {
                obj[firstK] = value; 
            }
        } else {
            if (firstK=='') {
                obj.push(value); 
            } else {
                if (!(firstK in obj)) {
                    obj[firstK]={};
                } 

                obj[firstK] = handleChild(obj[firstK], keysArr, value);
            }
        }

        return obj;
    };

    let result = {};
    for (const [key, value]  of formDataEntries ) {
        result= handleChild(result, key.split(/\[/), value);
    }
         
    return result;
}

// generic ajaxcall function 
function ajaxcall(endpoint, data) {
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(function (response) {
        return response.json();
    }).then(function (result) {
        console.log(result);
    });
}

// prevent all forms from being submitted and handle them as ajax call instead
var formObjects = document.getElementsByTagName('form');
for (var i = 0; i < formObjects.length; i++) {
    var formObject = formObjects[i];
    formObject.addEventListener('submit', function (event) {
        event.preventDefault();

		formSubmitter = event.submitter ? event.submitter : null;
		if (formSubmitter != null) {
			formJsonData = form2json(formObject);

			ajaxcall(
				formSubmitter.getAttribute('ajaxcall'),
				formJsonData
			);
		}
    });
}

// functionality for form selectors
var formSelectors = document.getElementsByClassName("w3-form-selector");
for (var i = 0; i < formSelectors.length; i++) {
    formSelectors[i].addEventListener('change', function() {
        if (this.checked) {
            var formSelectables = document.getElementsByClassName("w3-form-selectable");
            for (let i = 0; i < formSelectables.length; i++) {
                formSelectables.item(i).classList.add('w3-hide');
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