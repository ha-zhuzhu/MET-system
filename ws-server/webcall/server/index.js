<<<<<<< HEAD
const socket = require('socket.io');
const http = require('http');

const server = http.createServer()

const io = socket(server, {
    cors: {
        origin: '*' // 配置跨域
    }
});

io.on('connection', sock => {
    console.log('连接成功...')
    // 向客户端发送连接成功的消息
    sock.emit('connectionSuccess');

    sock.on('joinRoom', (roomId, user) => {
        sock.join(roomId);
        console.log(user + ' joinRoom-房间ID：' + roomId);
    })

    // 广播有人加入到房间
    sock.on('callRemote', (roomId) => {
        io.to(roomId).emit('callRemote', roomId)
    })

    // 广播同意接听视频
    sock.on('acceptCall', (roomId) => {
        io.to(roomId).emit('acceptCall')
    })

    // 接收offer
    sock.on('sendOffer', ({ offer, roomId }) => {
        io.to(roomId).emit('sendOffer', offer)
    })

    // 接收answer
    sock.on('sendAnswer', ({ answer, roomId }) => {
        io.to(roomId).emit('sendAnswer', answer)
    })

    // 收到candidate
    sock.on('sendCandidate', ({ candidate, reciever, roomId }) => {
        io.to(roomId).emit('sendCandidate', reciever, candidate)
    })

    // 挂断结束视频
    sock.on('hangUp', (roomId) => {
        io.to(roomId).emit('hangUp')
    })
})

server.listen(3000, () => {
    console.log('服务器启动成功');
});
=======
const socket = require('socket.io');
const http = require('http');

const server = http.createServer()

const io = socket(server, {
    cors: {
        origin: '*' // 配置跨域
    }
});

io.on('connection', sock => {
    console.log('连接成功...')
    // 向客户端发送连接成功的消息
    sock.emit('connectionSuccess');

    sock.on('joinRoom', (roomId, user) => {
        sock.join(roomId);
        console.log(user + ' joinRoom-房间ID：' + roomId);
    })

    // 广播有人加入到房间
    sock.on('callRemote', (roomId) => {
        io.to(roomId).emit('callRemote', roomId)
    })

    // 广播同意接听视频
    sock.on('acceptCall', (roomId) => {
        io.to(roomId).emit('acceptCall')
    })

    // 接收offer
    sock.on('sendOffer', ({ offer, roomId }) => {
        io.to(roomId).emit('sendOffer', offer)
    })

    // 接收answer
    sock.on('sendAnswer', ({ answer, roomId }) => {
        io.to(roomId).emit('sendAnswer', answer)
    })

    // 收到candidate
    sock.on('sendCandidate', ({ candidate, reciever, roomId }) => {
        io.to(roomId).emit('sendCandidate', reciever, candidate)
    })

    // 挂断结束视频
    sock.on('hangUp', (roomId) => {
        io.to(roomId).emit('hangUp')
    })
})

server.listen(3000, () => {
    console.log('服务器启动成功');
});
>>>>>>> 8fe26a4b4fdead9e5ca165b0089f41592f8ba15b
