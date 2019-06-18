function stimStart() {
    const mode = $("#stim_mode").val();
    const area = $("#brain_area").val();
    let silent;
    if ($("#silent_check").is(":checked")) {
        silent = "_silent";
        //alert("SILENT!!!!");
    } else {
        silent = "";
        //alert("shhhhh");
    }
    //alert(mode);
    if (mode === "sham") {
        $.get("/sham" + area + silent);
        //alert("/sham" + area + silent);
    } else {
        $.get("/start" + area + silent);
        //alert("/start" + area + silent);
    }
}
function stimStartPauseResume() {
    const btn = $("#start_pause_btn");
    //alert(btn.text());
    if (btn.text() === "START") {
        stimStart();
        btn.html("PAUSE");
    } else if (btn.text() === "PAUSE") {
        $.get("/pause");
        btn.html("RESUME");
    } else {
        $.get("/resume");
        btn.html("PAUSE");
    }
}
function stimStop() {
    $.get("/stop");
    $("#start_pause_btn").html("START");
}
function stimLower() {
    $("#current").load("/lower");
}
function stimHigher() {
    $("#current").load("/higher");
}
function tagClick() {
    $.get("/tag");
}
function showTimeCurrent() {
    $.get("/time_current", function(data){
        $("#timer").text(data.slice(0, 5));
        $("#current").text(data.slice(5, ));
        const btn = $("#start_pause_btn");
        if (data === "--:--0.0" && btn.text() === "PAUSE") {
            btn.html("START");
        }
    })
}

$(document).ready(function() {
    //$.ajaxSettings({
    //    async: true
    //});
    //$("#start_pause_btn").click(stimStartPauseResume);
    //$("#stop_btn").click(stimStop);
    //$("#btn_lower").click(stimLower);
    //$("#btn_higher").click(stimHigher);
    //$("#btn_click").click(tagClick);
    const intv = setInterval("showTimeCurrent()", 1000);
});