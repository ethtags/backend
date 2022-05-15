// This script gets injected into any opened page
// whose URL matches the pattern defined in the manifest
// (see "content_script" key).
// Several foreground scripts can be declared
// and injected into the same or different pages.


(async () => {
    
    const txId = window.location.href.split('/tx/')[1]

    const fromElem = document.getElementById("addressCopy")
    const toElem = document.getElementById("contractCopy")

    const fromAddress = fromElem.href.split('/address/')[1]
    const toAddress = toElem.href.split('/address/')[1]

    // TODO make + await + parse API requests with axios

    // TODO: build elems using createElement api
    // EX: 
    // elem = document.createElement("div")
    // elem.innerText("hello world")
    // fromElem.before(elem)



})()




console.log("This prints to the console of the page (injected only if the page url matched)")
debugger;