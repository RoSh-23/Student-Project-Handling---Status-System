function remFlashMessage(messageNo)
{
	var flashMessages = document.getElementsByClassName('flashed-messages');
	flashMessages[messageNo - 1].innerText = '';
}