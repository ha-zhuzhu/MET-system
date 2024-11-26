<<<<<<< HEAD
const WebSocket = require('ws');
const express = require('express');
const ffmpeg = require('fluent-ffmpeg');
const webSocketStream = require("websocket-stream/stream");

ffmpeg.setFfmpegPath("D:/tool/ffmpeg/bin/ffmpeg.exe");

const app = express();
const http = require('http');
const server = http.createServer(app);

// 存储流ID和相应的流
const streamMap = new Map();

// 设置 WebSocket 服务器
const wss = new WebSocket.Server({ server });

// WebSocket 连接处理
wss.on('connection', (ws) => {
    console.log('客户端已连接');

    let streamId = null;
    let ffmpegProcess;

    ws.on('message', (message) => {
        // console.log(message)
        try {
            if (Buffer.isBuffer(message)) {
                // console.log('收到二进制数据，忽略该消息');
                return; // 忽略二进制消息
            }

            const data = JSON.parse(message);
            console.log(data)
            if (data.type == "applyStream") {
                streamId = data.streamId;
                console.log(`接收到流ID: ${streamId}`);

                // 检查该流 ID 是否已经存在
                if (streamMap.has(streamId)) {
                    console.log('流 ID 已存在，删除之前的');
                    const { clients } = streamMap.get(streamId);
                    const index = clients.indexOf(ws);
                    if (index !== -1) clients.splice(index, 1); // 移除关闭的客户端
                    if (clients.length === 0) {
                        ffmpegProcess.kill(); // 如果没有客户端，停止 FFmpeg 进程
                        streamMap.delete(streamId); // 删除该流 ID
                    }
                }
                console.log('创建新的流');
                const stream = webSocketStream(ws, { binary: true });

                // 启动 FFmpeg 进程
                ffmpegProcess = ffmpeg()
                    .input(stream)
                    .inputFormat('webm')
                    // .outputFormat('flv')
                    .outputFormat('mpegts')
                    .videoCodec('libx264')
                    .audioCodec('aac')
                    .on('start', (commandLine) => {
                        console.log('FFmpeg命令:', commandLine);
                    })
                    .on('end', () => {
                        console.log('视频处理完毕');
                    })
                    .on('error', (err) => {
                        console.error('FFmpeg错误:', err);
                    });

                const ffmpegStream = ffmpegProcess.pipe();

                // 存储流 ID、FFmpeg 流和客户端列表
                streamMap.set(streamId, {
                    ffmpegStream,
                    clients: [ws] // 初始化客户端列表
                });

            }
            else if (data.type == "closeStream") {
                streamId = data.streamId;
                console.log(`WebSocket 保持连接，关闭流 ID: ${streamId}`);
                const { clients } = streamMap.get(streamId);
                const index = clients.indexOf(ws);
                if (index !== -1) clients.splice(index, 1); // 移除关闭的客户端
                if (clients.length === 0) {
                    ffmpegProcess.kill(); // 如果没有客户端，停止 FFmpeg 进程
                    streamMap.delete(streamId); // 删除该流 ID
                }
            }

        } catch (error) {
            console.error('无法解析消息:', error);
        }
    });

    // 监听 WebSocket 关闭事件
    ws.on('close', () => {
        console.log('websocket关闭')
        if (ffmpegProcess) {
            ffmpegProcess.kill(); // 关闭连接时终止对应的 FFmpeg 进程
        }
        // console.log(`WebSocket 连接关闭，流 ID: ${streamId}`);
        // const { clients } = streamMap.get(streamId);
        // const index = clients.indexOf(ws);
        // if (index !== -1) clients.splice(index, 1); // 移除关闭的客户端
        // if (clients.length === 0) {
        //     ffmpegProcess.kill(); // 如果没有客户端，停止 FFmpeg 进程
        //     streamMap.delete(streamId); // 删除该流 ID
        // }
    });
});

app.get('/Stream', (req, res) => {
    const streamId = req.query.streamId;
    if (!streamId || !streamMap.has(streamId)) {
        return res.status(404).send('流未找到');
    }
    // res.setHeader('Content-Type', 'video/x-flv');
    res.setHeader('Content-Type', 'video/mp2t');
    res.setHeader('Access-Control-Allow-Origin', '*'); // 设置 CORS
    console.log("流输出", req.query)
    // const { ffmpegStream } = streamMap.get(streamId);
    // ffmpegStream.pipe(res);
    const { ffmpegStream, clients } = streamMap.get(streamId);

    // 创建 FLV 流传输管道
    ffmpegStream.on('data', (chunk) => {
        try {
            res.write(chunk); // 将数据块写入响应
        } catch (err) {
            console.error('写入响应失败:', err);
        }
    });

    res.on('close', () => {
        console.log('客户端断开连接');
        res.end();
    });
});

// 启动服务器
server.listen(3001, () => {
    console.log('服务器运行在 http://localhost:3001');
});
=======
const WebSocket = require('ws');
const express = require('express');
const ffmpeg = require('fluent-ffmpeg');
const webSocketStream = require("websocket-stream/stream");

ffmpeg.setFfmpegPath("D:/tool/ffmpeg/bin/ffmpeg.exe");

const app = express();
const http = require('http');
const server = http.createServer(app);

// 存储流ID和相应的流
const streamMap = new Map();

// 设置 WebSocket 服务器
const wss = new WebSocket.Server({ server });

// WebSocket 连接处理
wss.on('connection', (ws) => {
    console.log('客户端已连接');

    let streamId = null;
    let ffmpegProcess;

    ws.on('message', (message) => {
        // console.log(typeof message,message)
        try {
            if (Buffer.isBuffer(message)) {
                // console.log('收到二进制数据，忽略该消息');
                return; // 忽略二进制消息
            }

            const data = JSON.parse(message);
            console.log(data)
            if (data.type == "applyStream") {
                streamId = data.streamId;
                console.log(`接收到流ID: ${streamId}`);

                // 检查该流 ID 是否已经存在
                if (streamMap.has(streamId)) {
                    console.log('流 ID 已存在，删除之前的');
                    const { clients } = streamMap.get(streamId);
                    const index = clients.indexOf(ws);
                    if (index !== -1) clients.splice(index, 1); // 移除关闭的客户端
                    if (clients.length === 0) {
                        ffmpegProcess.kill(); // 如果没有客户端，停止 FFmpeg 进程
                        streamMap.delete(streamId); // 删除该流 ID
                    }
                }
                console.log('创建新的流');
                const stream = webSocketStream(ws, { binary: true });

                // 启动 FFmpeg 进程
                ffmpegProcess = ffmpeg()
                    .input(stream)
                    .inputFormat('webm')
                    // .outputFormat('flv')
                    .outputFormat('mpegts')
                    .videoCodec('libx264')
                    .audioCodec('aac')
                    .on('start', (commandLine) => {
                        console.log('FFmpeg命令:', commandLine);
                    })
                    .on('end', () => {
                        console.log('视频处理完毕');
                    })
                    .on('error', (err) => {
                        console.error('FFmpeg错误:', err);
                    });

                const ffmpegStream = ffmpegProcess.pipe();

                // 存储流 ID、FFmpeg 流和客户端列表
                streamMap.set(streamId, {
                    ffmpegStream,
                    clients: [ws] // 初始化客户端列表
                });

            }
            else if (data.type == "closeStream") {
                streamId = data.streamId;
                console.log(`WebSocket 保持连接，关闭流 ID: ${streamId}`);
                const { clients } = streamMap.get(streamId);
                const index = clients.indexOf(ws);
                if (index !== -1) clients.splice(index, 1); // 移除关闭的客户端
                if (clients.length === 0) {
                    ffmpegProcess.kill(); // 如果没有客户端，停止 FFmpeg 进程
                    streamMap.delete(streamId); // 删除该流 ID
                }
            }

        } catch (error) {
            console.error('无法解析消息:', error);
        }
    });

    // 监听 WebSocket 关闭事件
    ws.on('close', () => {
        console.log('websocket关闭')
        if (ffmpegProcess) {
            ffmpegProcess.kill(); // 关闭连接时终止对应的 FFmpeg 进程
        }
        // console.log(`WebSocket 连接关闭，流 ID: ${streamId}`);
        // const { clients } = streamMap.get(streamId);
        // const index = clients.indexOf(ws);
        // if (index !== -1) clients.splice(index, 1); // 移除关闭的客户端
        // if (clients.length === 0) {
        //     ffmpegProcess.kill(); // 如果没有客户端，停止 FFmpeg 进程
        //     streamMap.delete(streamId); // 删除该流 ID
        // }
    });
});

app.get('/Stream', (req, res) => {
    const streamId = req.query.streamId;
    if (!streamId || !streamMap.has(streamId)) {
        return res.status(404).send('流未找到');
    }
    // res.setHeader('Content-Type', 'video/x-flv');
    res.setHeader('Content-Type', 'video/mp2t');
    res.setHeader('Access-Control-Allow-Origin', '*'); // 设置 CORS
    console.log("流输出", req.query)
    // const { ffmpegStream } = streamMap.get(streamId);
    // ffmpegStream.pipe(res);
    const { ffmpegStream, clients } = streamMap.get(streamId);

    // 创建 FLV 流传输管道
    ffmpegStream.on('data', (chunk) => {
        try {
            res.write(chunk); // 将数据块写入响应
        } catch (err) {
            console.error('写入响应失败:', err);
        }
    });

    res.on('close', () => {
        console.log('客户端断开连接');
        res.end();
    });
});

// 启动服务器
server.listen(3001, '0.0.0.0', () => {
    console.log('服务器运行在 http://localhost:3001');
});
>>>>>>> 8fe26a4b4fdead9e5ca165b0089f41592f8ba15b
