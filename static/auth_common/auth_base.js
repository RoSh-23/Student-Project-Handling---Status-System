function hdNavDdownsTog(num)
{
	var dropdown = 'ddown' + String(num)  
	document.getElementById(dropdown).classList.toggle('show-ddown');
}

window.onclick = function(event) 
{
  	if (!event.target.matches('.hd-nav-ddowns-btn')) 
  	{
    	var dropdowns = document.getElementsByClassName('ddowns-content');
    	var i;
    	for (i = 0; i < dropdowns.length; i++) 
    	{
      		var openDropdown = dropdowns[i];
      		if (openDropdown.classList.contains('show-ddown')) 
      		{
        		openDropdown.classList.remove('show-ddown');
      		}
    	}
  	}
}


function func(num) 
{
	var n = Number(num)
	var dropdowns = document.getElementsByClassName('ddowns-content');
	var i;
	for (i = 0; i < dropdowns.length; i++) 
	{
		if( i != n)
		{
			var openDropdown = dropdowns[i];
  			if (openDropdown.classList.contains('show-ddown')) 
  			{
    			openDropdown.classList.remove('show-ddown');
  			}
		}
	}
}


function remFlashMessage(messageNo)
{
	var flashMessages = document.getElementsByClassName('flashed-messages');
	flashMessages[messageNo - 1].innerText = ' ';
}