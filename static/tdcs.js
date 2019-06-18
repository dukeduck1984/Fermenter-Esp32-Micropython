var xmlhttp;
if (window.XMLHttpRequest)
{
    //  IE7+, Firefox, Chrome, Opera, Safari 浏览器执行代码
    xmlhttp=new XMLHttpRequest();
}
else
{
    // IE6, IE5 浏览器执行代码
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
}
function stimStart()
{
    // get the stimulation mode
    var drop_menu = document.getElementById("stim_mode");
    var index = drop_menu.selectedIndex;
    var mode = drop_menu.options[index].value;
    if (mode == "sham") {  // Sham stimulation
        xmlhttp.open("GET","/sham",true);
        xmlhttp.send();
    } else {  // Anode stimulation
        xmlhttp.open("GET","/start",true);
        xmlhttp.send();
    }
}
function stimStartPauseResume()
{
    var btn = document.getElementById("start_pause_btn");
    if (btn.innerHTML == "START"){
        stimStart();
        btn.innerHTML = "PAUSE";
    } else if (btn.innerHTML == "PAUSE"){
        xmlhttp.open("GET","/pause",true);
        xmlhttp.send();
        btn.innerHTML = "RESUME";
    } else {
        xmlhttp.open("GET","/resume",true);
        xmlhttp.send();
        btn.innerHTML = "PAUSE";
    }

}
function stimStop()
{
    var btn = document.getElementById("start_pause_btn");
    xmlhttp.open("GET","/stop",true);
    xmlhttp.send();
    btn.innerHTML = "START";
}
function stimLower() {
    xmlhttp.onreadystatechange = function()
    {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            document.getElementById("current").innerHTML = xmlhttp.responseText;
        }
    };
    xmlhttp.open("GET", "/lower", true);
    xmlhttp.send();
}
function stimHigher() {
    xmlhttp.onreadystatechange = function()
    {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            document.getElementById("current").innerHTML = xmlhttp.responseText;
        }
    };
    xmlhttp.open("GET", "/higher", true);
    xmlhttp.send();
}
function tagClick() {
    xmlhttp.open("GET", "/tag", true);
    xmlhttp.send();
}
function showTimeCurrent(){
    xmlhttp.onreadystatechange = function()
    {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            var result = xmlhttp.responseText;
            document.getElementById("timer").innerHTML = result.slice(0, 5);
            document.getElementById("current").innerHTML = result.slice(5, )
        }
    };
    xmlhttp.open("GET", "/time_current", true);
    xmlhttp.send();
}
var current = self.setInterval("showTimeCurrent()", 1000);