

function doGet(e) {
  Logger.log("here in get");
//    var jsonString = request.postData.getDataAsString();
//    var jsonData = JSON.parse(jsonString);
//    sheet.appendRow([ 'Data1:' , jsonData.Data1 ]); // Just an example
    return ContentService.createTextOutput('Hello, world get2!');

}

function doPost(e) {
  Logger.log("here in post");
//    var jsonString = request.postData.getDataAsString();
//    var jsonData = JSON.parse(jsonString);
//    sheet.appendRow([ 'Data1:' , jsonData.Data1 ]); // Just an example
  main();
    return ContentService.createTextOutput('Hello, world post!');

}

function main() {
//   var jsonString = e.postData.getDataAsString();
//   var jsonData = JSON.parse(jsonString);
//   sheet.appendRow([ 'Data1:' , jsonData.Data1 ]); // Just an example
  
  var ss = SpreadsheetApp.openById("1hwl0E9_bRN-VebgRmThyxznAYGCKKIdJWKwI2CnOT88");
  
  var d = new Date();
  var currentTime = d.toLocaleTimeString(); 
  
  var newSS = ss.copy(currentTime + ss.getName());
   Logger.log(newSS.getUrl());
  
  var tmpJson= {
    "title": "1111111111111111",
    "description": "22222222222222222222222"
  };  
  var sheet = newSS.getActiveSheet();
   writeJSONtoSheet(tmpJson,sheet);

   sheet.appendRow([ 'Data1:' ,'aaaaaaaaaaaaaaaaa' ]);
  
  tmpJson= {
    "title": "3333333333333333333",
    "description": "4444444444444444444444"
  };    
   writeJSONtoSheet(tmpJson,sheet);
  
  
  var tmpRes = UrlFetchApp.fetch("http://calvinzhu.pythonanywhere.com/todo/api/v1.0/tasks");
  Logger.log('return Json sample1:' + tmpRes);
  

  writeJSONtoSheet(tmpRes,sheet);
}


// Written by Amit Agarwal www.ctrlq.org
 
function writeJSONtoSheet(json,sheet) {
 
//  var sheet = SpreadsheetApp.getActiveSheet();
 
  var keys = Object.keys(json).sort();
  var last = sheet.getLastColumn();
  var header = sheet.getRange(1, 1, 1, last).getValues()[0];
  var newCols = [];
 
  for (var k = 0; k < keys.length; k++) {
    if (header.indexOf(keys[k]) === -1) {
      newCols.push(keys[k]);
    }
  }
 
  if (newCols.length > 0) {
    sheet.insertColumnsAfter(last, newCols.length);
    sheet.getRange(1, last + 1, 1, newCols.length).setValues([newCols]);
    header = header.concat(newCols);
  }
 
  var row = [];
 
  for (var h = 0; h < header.length; h++) {
    row.push(header[h] in json ? json[header[h]] : "");
  }
 
  sheet.appendRow(row);
 
}
