var ws = new WebSocket(" wss://h6zxetfwdd.execute-api.ap-southeast-1.amazonaws.com/production");
const labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
let labelIndex = 0;
// A marker with a with a URL pointing to a PNG.
var dict={};
var image = "";
var len = 0
var bomma=0;
function image_receiver(data) {
    data = data.data;
    data = JSON.parse(data);
    var key = data.message.split(" ")[0]
    if (key == 'DETECTEDIMAGES') {
        image += data.message.split(" ")[1]
    }
    if (key == 'DETECTEDOVER') {
        dict[bomma]=image;
        bomma=bomma+1;
        if(bomma==localStorage.getItem("count"))
        {
            showImages();
        }
        image="";
    }
}

ws.onmessage = image_receiver
function image_sender() {
        var msg = '{"action": "sendmessage", "message": "SENDIMAGES"}';
    ws.send(msg)
}
function showImages() {
    var miniClass = document.querySelector('.mini');
    for(let i = 0; i < Object.keys(dict).length; i++){
        console.log(dict[i]);
        miniClass.innerHTML +=  ` <img src="${"data:image/jpg;base64," + dict[i]}" alt = "${dict[i]}"  width="500" height="500" style="border: 2px solid red"> `;
      }
    }