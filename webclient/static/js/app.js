// get the Sidebar
var sidebar = document.getElementById("ui_sidebar");

// get the DIV with overlay effect
var overlay = document.getElementById("ui_overlay");

// empty click handler
function emptyClickHandler(event) {
	event.preventDefault();
	event.stopPropagation();
}

// toggle between showing and hiding the sidebar, and add overlay effect
function w3_open() {
    if (sidebar.classList.contains('w3-hide-medium')) {
        sidebar.classList.add('w3-show');
		sidebar.classList.remove('w3-hide-medium');
		
        overlay.classList.add('w3-show')
		overlay.classList.remove('w3-hide');
    } else {
        sidebar.classList.add('w3-hide-medium');
		sidebar.classList.remove('w3-show');
		
        overlay.classList.add('w3-hide');
		overlay.classList.remove('w3-show');
    }
}

// tlose the sidebar with the close button
function w3_close() {
    sidebar.classList.add('w3-hide');
    overlay.classList.add('w3-hide');
}

// show modal with text
function w3_modal(level, title, message) {
	let modal = document.getElementById('ui_modal');
	let modalHeader = modal.querySelector('header');
	let modalTitle = document.getElementById('ui_modal_title');
	let modalMessage = document.getElementById('ui_modal_message');
	
	modalTitle.innerHTML = title;
	modalMessage.innerHTML = message;
	
	modalHeader.classList.remove('w3-pale-red');
	modalHeader.classList.remove('w3-pale-yellow');
	modalHeader.classList.remove('w3-pale-green');
	
	if (level == 'error') {
		modalHeader.classList.add('w3-pale-red');
	} else if (level == 'warning') {
		modalHeader.classList.add('w3-pale-yellow');
	} else if (level == 'success') {
		modalHeader.classList.add('w3-pale-green');
	} else {
		//modalHeader.classList.add('w3-pale-red');
	}
	
	modal.classList.add('w3-show');
}

function w3_lock() {
	let lockableElements = document.getElementsByClassName('w3-lockable');
	for (let i = 0; i < lockableElements.length; i++) {
		let lockableElement = lockableElements[i];
		
		lockableElement.classList.add('w3-locked');
		lockableElement.setAttribute('disabled', 'disabled');
		lockableElement.addEventListener('click', emptyClickHandler);
	}
	
	let loadingElements = document.getElementsByClassName('w3-loading');
	for (let i = 0; i < loadingElements.length; i++) {
		let loadingElement = loadingElements[i];
		loadingElement.classList.remove('w3-hide');
	}
	
	window.onbeforeunload = function() {
		return true;
	};
}

function w3_unlock() {
	let lockableElements = document.getElementsByClassName('w3-lockable');
	for (let i = 0; i < lockableElements.length; i++) {
		let lockableElement = lockableElements[i];
		
		lockableElement.classList.remove('w3-locked');
		lockableElement.removeAttribute('disabled');
		lockableElement.removeEventListener('click', emptyClickHandler);
	}
	
	let loadingElements = document.getElementsByClassName('w3-loading');
	for (let i = 0; i < loadingElements.length; i++) {
		let loadingElement = loadingElements[i];
		loadingElement.classList.add('w3-hide');
	}
	
	window.onbeforeunload = null;
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
            if (firstK == '') {
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
	w3_lock();
	
    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(function (response) {
		if (response.ok) {
			return response.json();
		} else {
			w3_modal('error', 'Fehler beim Ausführen der Aktion!', 'Beim Ausführen der Funktion im WebClient ist ein Fehler aufgetreten.');
		}
    }).then(function (result) {
		if (result.code != 0) {
			w3_modal('error', 'Fehler beim Ausführen der Aktion!', result.message + ' (Fehlercode: ' + result.code + ')');
		}
		
		w3_unlock();
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