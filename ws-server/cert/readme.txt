生成用来登录https的crt和key（其余文件是用来辅助生成）

参考地址：https://cloud.tencent.com/developer/article/1552511

具体命令：

openssl genrsa -des3 -out server.key 2048

openssl req -new -x509 -key server.key -out ca.crt -days 3650

openssl req -new -key server.key -out server.csr

openssl x509 -req -days 3650 -in server.csr -CA ca.crt -CAkey server.key -CAcreateserial -out server.crt

其中使用的4位密码：1234


另一个：
https://www.cnblogs.com/java365/articles/17582496.html