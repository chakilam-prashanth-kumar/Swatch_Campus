var ws = new WebSocket("wss://h6zxetfwdd.execute-api.ap-southeast-1.amazonaws.com/production");
const labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
let labelIndex = 0;
// A marker with a with a URL pointing to a PNG.
var count = 0;
var dict={};

function initMap(lat, lng) {
    var myLatlng = new google.maps.LatLng(lat, lng);
    var map = new google.maps.Map(document.getElementById("map_canvas"), {
        zoom: 19,
        // draggable: true,
        path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
        center: myLatlng,
        animation: google.maps.Animation.DROP,
        mapTypeId: 'satellite'
    });

    // This event listener calls addMarker() when the map is clicked.
    google.maps.event.addListener(map, "click", (event) => {
            addMarker(event.latLng, map);
            // kmitmarker(event.latLng,map);
            document.getElementById("lat").value = event.latLng.lat();
            document.getElementById("long").value = event.latLng.lng();
            count += 1;
            myFunction();
            if (count > 1) {
                retreive(map);
            }
        })
        // Add a marker at the center of the map.
        //   addMarker(bangalore, map);
}
navigator.geolocation.getCurrentPosition(
    function(position) {
        google.maps.event.addDomListener(window, "load", initMap(position.coords.latitude, position.coords.longitude));
    },
    function errorCallback(error) {
        google.maps.event.addDomListener(window, "load", initMap(17.3970937, 78.4899736));
    }
);

// Adds a marker to the map.
function addMarker(location, map) {
    // Add the marker at the clicked location, and add the next-available label
    // from the array of alphabetical characters.
    new google.maps.Marker({
        position: location,
        animation: google.maps.Animation.DROP,
        label: labels[labelIndex++ % labels.length],
        map: map,
    });
}

function myFunction() {
    var table = document.getElementById("myTable");

    var row = table.insertRow(count);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);
    var cell4 = row.insertCell(3);
    var cell5 = row.insertCell(4);
    // cell1.outerHTML="<li class='list-inline-item'><button class='btn btn-danger btn-sm rounded-0' type='button' data-toggle='tooltip' data-placement='top' title='Delete'><i class='fa fa-trash'></i></button></li>"
    cell1.innerHTML = count;
    cell2.innerHTML = document.getElementById("lat").value;
    cell3.innerHTML = document.getElementById("long").value;
    cell4.outerHTML = "<th contenteditable='true'>8</th>"
    cell5.outerHTML = "<th contenteditable='true'>5</th>"
}

function retreive(map) {
    var lat0 = document.getElementById("myTable").rows[count - 1].cells[1].innerHTML;
    var long0 = document.getElementById("myTable").rows[count - 1].cells[2].innerHTML;
    var lat1 = document.getElementById("myTable").rows[count].cells[1].innerHTML;
    var long1 = document.getElementById("myTable").rows[count].cells[2].innerHTML;
    var lineCoordinates = [new google.maps.LatLng(lat0, long0), new google.maps.LatLng(lat1, long1)];
    var lineSymbol = {
        // // path: 'M 0,-2 0,1',
        // strokeOpacity: 1,
        // scale: 4
        path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
        // strokeColor: "#00008B",
        // fillColor: "#00008B",
        fillOpacity: 1.0
    };
    var line = new google.maps.Polyline({
        path: lineCoordinates,
        strokeOpacity: 0,
        icons: [{
            icon: lineSymbol,
            offset: "100%",
            repeat: '20px'
        }],
        map: map
    });
}

function tableToJson(table) {
    var data = [];
    var dict = {}
        // first row needs to be headers
    var headers = [];
    for (var i = 0; i < table.rows[0].cells.length; i++) {
        headers[i] = table.rows[0].cells[i].innerHTML.toLowerCase().replace(/ /gi, '');
    }

    // go through cells
    for (var i = 1; i < table.rows.length; i++) {

        var tableRow = table.rows[i];
        var rowData = {};

        for (var j = 0; j < tableRow.cells.length; j++) {

            rowData[headers[j]] = tableRow.cells[j].innerHTML.replace(/<\s*\/?\s*br\s*.*?>/g, '');

        }

        data.push(rowData);
    }
    dict['json'] = data;
    return dict;
}

function pull() {
    if (confirm("Are you sure")) {
        if (count > 0) {
            localStorage.setItem("count", count);
            var myjson = JSON.stringify(tableToJson(document.getElementById("myTable")));
            // document.querySelector("input[name='upload']").value=myjson;
            //downloadObjectAsJson(myjson,"Swach-Json-File")
            // document.querySelector("form").submit();
            console.log(myjson);
            var msg = '{"action": "sendmessage", "message": ' + myjson + '}';
            ws.send(msg)
        } else {
            alert("Atleast one point need to be selected!!");

        }
    }

}
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
        if(bomma==count)
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
function downloadObjectAsJson(exportObj, exportName) {
    var b = JSON.stringify(exportObj);
    str = b.replace(/\\/g, '');
    var dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(str);
    var downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", exportName + ".json");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
}

function openNav() {
    document.getElementById("mySidenav").style.width = "250px";
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}


window.initMap = initMap;