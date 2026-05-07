// Reference: https://stackoverflow.com/questions/56451370/how-to-get-pixel-number-from-image-by-click 

myimage.onclick = function(e) {
  var ratioX = e.target.naturalWidth / e.target.offsetWidth;
  var ratioY = e.target.naturalHeight / e.target.offsetHeight;

  var domX = e.x + window.pageXOffset - e.target.offsetLeft;
  var domY = e.y + window.pageYOffset - e.target.offsetTop;

  var imgX = Math.floor(domX * ratioX);
  var imgY = Math.floor(domY * ratioY);

  console.log(imgX, imgY);
};

// Another method
// myimage.onclick = function(e) {
//     var ratioX = e.target.naturalWidth / e.target.offsetWidth;
//     var ratioY = e.target.naturalHeight / e.target.offsetHeight;
// 
//     var imgX = Math.round(e.offsetX * ratioX);
//     var imgY = Math.round(e.offsetY * ratioY);
// 
//     console.log(imgX, imgY);
// };

