var checkPwdcheckPwdFlag = 1; // 1 -> no error | 0 - > yes error

function checkPwd(elem){
	var password = document.getElementById('pwd');
	if(elem.value.length > 0){
		if(elem.value != password.value){
			document.getElementById('pwd-alert').innerText = 'Confirm password does not match.';
			checkPwdFlag = 0;
		}
		else{
			document.getElementById('pwd-alert').innerText = '';
			checkPwdFlag = 1;
		}
	}else{
		document.getElementById('pwd-alert').innerText = 'Please enter confirm password.';
		checkPwdFlag = 0;
	}
}

function validateSamePwd() {
	if(checkPwdFlag == 1){
		return true;
	}else{
		return false;
	}
}