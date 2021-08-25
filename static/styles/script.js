const open = document.getElementById('selector');
const popup_container = document.getElementById('popup_container');
const close = document.getElementById('close');

open.addEventListener('click', () => {
	popup_container.classList.add('show');
})

close.addEventListener('click', () => {
	popup_container.classList.remove('show');
})

window.onload	= () => {
	const pickBtn = document.querySelector("#pick-btn")
	pickBtn.addEventListener("click",()=>{
		const fileInput = document.querySelector("#file-input")
		 console.log(fileInput)
		 if(fileInput){
			 fileInput.click()
		 }
	})
	const alertComp = document.querySelector(".alert");
	if(alertComp){
		setTimeout(()=>{
		alertComp.remove()
		},3000)
	}
}