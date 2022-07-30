function genRollNoInputElement(elem)
{

	var numOfMem = elem.value;
	const container = document.getElementById('roll-no-container');

	while (container.firstChild) 
	{
    	container.removeChild(container.lastChild);
  	}

	for (var i = 1; i <= numOfMem; i++) 
	{	
		const divElement = document.createElement('div');
		divElement.setAttribute('class', 'roll-no-div');

		const labelElement = document.createElement('label');
		var elementNameStr = 'roll-no' + String(i);
		labelElement.setAttribute('for', elementNameStr);
		labelElement.setAttribute('class', 'roll-no-input-label');
		labelElement.innerHTML = 'Member ' + String(i) + ' Roll Number*';

		if (i == 1)
		{
			labelElement.innerHTML = 'Member ' + String(i) + ' Roll Number*' + '<div id="myDiv">(Leader Roll Number)</div>' 
		}

		const inputElement = document.createElement('input');
		inputElement.setAttribute('name', elementNameStr);
		inputElement.setAttribute('type', 'number');
		inputElement.setAttribute('min', 1);
		inputElement.setAttribute('step', 1);
		inputElement.setAttribute('required', 'true');
		inputElement.setAttribute('class', 'roll-no-input');
		inputElement.setAttribute('onchange', 'checkRollNos()');


		divElement.appendChild(labelElement);
		divElement.appendChild(inputElement);

		container.appendChild(divElement);
	}
}



function checkRollNos() 
{
	var uniqRollFlag = 1;
	var rollNosElems = document.getElementsByClassName('roll-no-input');
	var rollNosElems2 = rollNosElems;

	var rn = [];
	for (var i = 0; i < rollNosElems.length; i++)
	{
		rn[i] = rollNosElems[i].value;
	}

	var rn2 = rn;

	for (var i = 0; i < rn.length; i++)
	{
		if (uniqRollFlag == 0)
			break;
		if (rollNosElems[i].value.length > 0) 
		{
			for(var j = 0; j < rn2.length; j++)
			{
				if(i != j)
				{
					if(rn[i] === rn2[j])
					{
						document.getElementById('roll-unique-alert').innerText = 'Enter unique roll numbers.';
						uniqRollFlag = 0;
						break;
					}
					else
					{
						document.getElementById('roll-unique-alert').innerText = '';
						uniqRollFlag = 1;
					}
				}
			}
		}
		else
		{
			document.getElementById('roll-unique-alert').innerText = 'Please enter roll numbers.';
			uniqRollFlag = 0;
			break;
		}
	}
	if (uniqRollFlag == 0)
		return false;
	else 
		return true;
}

function validateUniqRoll() 
{
	if(uniqRollFlag == 1)
	{
		return true;
	}
	else
	{
		return false;
	}
}