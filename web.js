//node.js 提供文件服务

// 文件服务器

const express = require("express");
const bodyparser = require("body-parser");
const fs = require("fs");
const path = require("path");

var app = express();

// CORS
app.all('*', function (req, res, next) {
    res.header('Access-Control-Allow-Origin', 'https://teclab.org.cn');
    res.header('Access-Control-Allow-Origin', 'http://192.168.1.4:7080');
    res.header('Access-Control-Allow-Headers', 'Content-Type');
    res.header('Access-Control-Allow-Methods', 'POST,GET');
    res.header('Access-Control-Allow-Credentials', 'true');
    next();
});

// 静态文件服务
app.use(express.static(path.join(__dirname, "web")));
app.use(bodyparser.urlencoded({ extended: false }));



app.get("/api/projects", function (req, res) {
    // 读取文件并返回
    var data;
    try {
        data = fs.readFileSync(path.join(__dirname, "data", "projects.json"));
    } catch (error) {
        data = "[]";
    }
    res.send(data);
});


app.listen(80, function () {
    console.log("Start");
});

