function showThisModal(modNum)
{
    var modString = '#modal' + String(modNum);
    const modal = document.querySelector(modString);
    modal.classList.toggle("show-modal");      
}

function closeThisModal(modNum) 
{
    var closeButtonString = '#modal-close-button' + String(modNum);
    var modString = '#modal' + String(modNum);
    const modal = document.querySelector(modString);
    const closeButton = document.querySelector(closeButtonString);
    modal.classList.toggle("show-modal");      
}