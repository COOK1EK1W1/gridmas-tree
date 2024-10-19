function enable(){
  buttons = document.getElementsByClassName("pattern-button")
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].removeAttribute("disabled");
  }
}

function clicked(){
  cooldown = true
  setTimeout(()=>enable(), 5000)
  buttons = document.getElementsByClassName("pattern-button")
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].setAttribute("disabled", "");
  }

}
